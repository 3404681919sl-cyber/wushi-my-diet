"""DeepSeek V4 Pro 食谱生成层（T3）。

设计定位
--------
- 贝叶斯内核（``services/tolerance`` + ``services/conflict`` + ``services/safety``，
  已在 T2 实现）= **约束来源**：负责安全剂量 / 硬冲突判定。
- DeepSeek V4 Pro = **食谱生成层**：按多目标权重 + 个性化约束，生成"可口"食谱。
- 两者组合：LLM 拿到约束后产出食谱；任何异常 / 缺 key → 返回 ``None``，
  交给路由回退到 T2 的模板生成（``template.generate_recipe``）。

安全红线（可上市级）
-------------------
- API key 仅服务端持有，**绝不**下发明文到小程序端；函数内不记录 key。
- 无 key / 网络超时 / 解析失败 / 任何异常 → 一律返回 ``None``，绝不向客户端抛错。
- LLM 返回结果做防御式清洗：硬性冲突（🔴）食物一律丢弃，安全等级归一为
  green / yellow / red，用量取整，字段缺失则补齐，最终结构可直接喂 ``RecipeOut``。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.condition import Condition
from app.models.food import Food
from app.models.symptom import SymptomDef, SymptomLog
from app.services.conflict.engine import compute_conflicts
from app.services.tolerance.model import get_threshold_values

logger = logging.getLogger(__name__)

# DeepSeek V4 Pro：legacy deepseek-chat / deepseek-reasoner 已于 2026-07-24 弃用。
_DEEPSEEK_MODEL = "deepseek-v4-pro"
_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
# 单次生成超时（秒），避免阻塞请求链路。
_LLM_TIMEOUT = 20.0

# 合法安全等级集合（小写）。
_VALID_SAFETY = {"green", "yellow", "red"}


async def generate_recipe_llm(
    session: AsyncSession,
    user_id: int,
    target_weights: Optional[dict] = None,
    body_state: Optional[str] = None,
    exclude_food_ids: Optional[List[int]] = None,
    api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """调用 DeepSeek V4 Pro 生成个性化食谱。

    Args:
        session: 异步数据库会话（用于读取用户个性化约束）。
        user_id: 用户 ID。
        target_weights: 目标权重，如 ``{"gut": 0.7, "glucose": 0.2, "fat_loss": 0.1}``。
        body_state: 近期身体状态备注（可选）。
        exclude_food_ids: 需排除的食物 ID 列表（可选）。
        api_key: DeepSeek API key（服务端持有）。为 ``None`` 时直接回退模板。

    Returns:
        结构兼容 ``RecipeOut`` 的字典：
        ``{title, note, items:[{food_id, name, amount_g, safety, replaceable_with, reason}]}``。
        无 key / 任意异常 → 返回 ``None``（由调用方回退模板）。
    """
    # 无 key 直接短路，避免任何网络动作（也保证测试环境零副作用）。
    if not api_key:
        return None

    # 惰性导入：openai 未安装时安全回退模板，而非让整个应用无法导入。
    try:
        from openai import AsyncOpenAI
    except Exception:  # pragma: no cover - 依赖缺失保护
        logger.warning("openai SDK 未安装，LLM 食谱不可用，回退模板")
        return None

    try:
        # 1) 收集用户个性化约束（贝叶斯内核产出）。
        context = await _collect_context(session, user_id, exclude_food_ids)
        # 2) 组装结构化 Prompt。
        messages = _build_messages(context, target_weights, body_state, exclude_food_ids)
        # 3) 调用 DeepSeek（OpenAI 兼容接口）。
        client = AsyncOpenAI(api_key=api_key, base_url=_DEEPSEEK_BASE_URL)
        try:
            resp = await client.chat.completions.create(
                model=_DEEPSEEK_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                timeout=_LLM_TIMEOUT,
            )
        finally:
            # 无论成功/超时/异常，都及时关闭底层连接，避免悬挂请求。
            try:
                await client.close()
            except Exception:
                pass
        content = resp.choices[0].message.content if resp.choices else None

        # 4) 健壮解析 + 防御式清洗。
        recipe = _parse_and_normalize(
            content,
            red_food_ids=context["red_food_ids"],
            name_to_id=context["name_to_id"],
            body_state=body_state,
        )
        return recipe
    except Exception as exc:  # 任何异常都静默回退，绝不外抛。
        logger.warning("DeepSeek 食谱生成失败，回退模板：%s", exc)
        return None


async def _collect_context(
    session: AsyncSession,
    user_id: int,
    exclude_food_ids: Optional[List[int]],
) -> Dict[str, Any]:
    """收集注入给 LLM 的个性化约束。

    返回 ``{conditions, catalog, red_food_ids, name_to_id, symptoms}``。
    - ``conditions``：用户激活病症及其 fodmap / glucose / histamine 禁忌标志。
    - ``catalog``：候选食物目录（含 id、安全等级、个性化剂量、FODMAP/GL/组胺）。
    - ``red_food_ids``：硬性冲突食物 ID 集合（防御式丢弃用）。
    - ``name_to_id``：食物名 → id 映射（LLM 只给名字时回解 id）。
    - ``symptoms``：近期症状（严重度）。
    """
    exclude = set(exclude_food_ids or [])

    # ---- 激活病症 ----
    conditions = list(
        await session.scalars(
            select(Condition).where(
                Condition.user_id == user_id, Condition.is_active.is_(True)
            )
        )
    )
    cond_list: List[Dict[str, Any]] = []
    for c in conditions:
        flags: dict = c.fodmap_flags or {}
        fodmap_forbidden = [dim for dim, on in flags.items() if on]
        cond_list.append(
            {
                "name": c.name,
                "fodmap_forbidden": fodmap_forbidden,
                "glucose_forbidden": bool(c.glucose_flag),
                "histamine_forbidden": bool(c.histamine_flag),
            }
        )

    # ---- 食物目录（含安全等级 + 个性化剂量）----
    foods = list(await session.scalars(select(Food)))
    catalog: List[Dict[str, Any]] = []
    red_food_ids: set = set()
    name_to_id: Dict[str, int] = {}
    for f in foods:
        if f.id in exclude:
            continue
        conflicts = await compute_conflicts(session, user_id, f)
        hard_conflicts = [cf for cf in conflicts if cf.get("hard")]
        if hard_conflicts:
            red_food_ids.add(f.id)
            safety_level = "red"
        else:
            tv = await get_threshold_values(user_id, f.id, session, persist=False)
            if tv["n_obs"] == 0:
                safety_level = "yellow"
            elif tv["unsafe_g"] < 10:
                safety_level = "red"
                red_food_ids.add(f.id)
            elif tv["safe_g"] >= 30:
                safety_level = "green"
            else:
                safety_level = "yellow"

        high_fodmap = [
            dim for dim, lvl in (f.fodmap_category or {}).items() if lvl == "high"
        ]
        catalog.append(
            {
                "id": f.id,
                "name": f.name,
                "safety": safety_level,
                "high_fodmap_dims": high_fodmap,
                "gi": f.gi,
                "histamine_level": f.histamine_level,
                "gl_per_100g": f.gl_per_100g,
            }
        )
        name_to_id[f.name] = f.id

    # ---- 近期症状（最近 10 条）----
    symptom_rows = list(
        await session.scalars(
            select(SymptomLog)
            .where(SymptomLog.user_id == user_id)
            .order_by(SymptomLog.logged_at.desc())
            .limit(10)
        )
    )
    symptoms: List[Dict[str, Any]] = []
    for s in symptom_rows:
        defn = await session.get(SymptomDef, s.symptom_def_id)
        symptoms.append(
            {"symptom": defn.name if defn else "未知症状", "severity": s.severity}
        )

    return {
        "conditions": cond_list,
        "catalog": catalog,
        "red_food_ids": red_food_ids,
        "name_to_id": name_to_id,
        "symptoms": symptoms,
    }


def _build_messages(
    context: Dict[str, Any],
    target_weights: Optional[dict],
    body_state: Optional[str],
    exclude_food_ids: Optional[List[int]],
) -> List[Dict[str, str]]:
    """组装 system + user 消息（结构化 Prompt）。"""
    system_prompt = (
        "你是吾食(Wushi)的资深营养师 AI，专注 IBS / 多病矛盾的饮食不耐受管理。"
        "你的任务是根据用户的多目标权重与个性化安全约束，设计一份『可口且安全』的食谱。"
        "你只需输出一个严格合法的 JSON 对象，禁止输出任何额外说明文字。"
        "JSON 结构必须如下：\n"
        "{\n"
        '  "title": "食谱标题（简短）",\n'
        '  "note": "给用户的简短提示（可空字符串）",\n'
        '  "items": [\n'
        "    {\n"
        '      "food_id": 食物ID（必须是候选目录中给出的 id；若确实未知给 null）,\n'
        '      "name": "食物名称（必须与候选目录一致）",\n'
        '      "amount_g": 用量（克，整数）,\n'
        '      "safety": "green 或 yellow 或 red（必须用候选目录给出的安全等级）",\n'
        '      "replaceable_with": ["可替换食物名称数组（可空）"],\n'
        '      "reason": "选用理由（一句话，中文）"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "硬约束（务必遵守）：\n"
        "① 安全等级为 red（硬性冲突）的食物一律不得出现在食谱中；\n"
        "② 每种食物用量不得超过其 safe_g（或至多达到 caution_g 并标注『限量』）；\n"
        "③ 优先选用 green 食物；\n"
        "④ 可探索性插入少量 yellow 食物，并明确标注为小剂量；\n"
        "⑤ 关注组合 FODMAP 总负荷与血糖负荷(GL)，避免多种高负荷食物叠加导致预警；\n"
        "⑥ 输出必须是合法 JSON，字段名与上面完全一致。"
    )

    user_prompt = (
        "【目标权重】\n"
        f"{json.dumps(target_weights or {'gut': 0.7, 'glucose': 0.2, 'fat_loss': 0.1}, ensure_ascii=False)}\n\n"
        "【用户激活病症与禁忌】\n"
        f"{json.dumps(context['conditions'], ensure_ascii=False)}\n\n"
        "【候选食物目录（含个性化安全等级与剂量约束）】\n"
        f"{json.dumps(context['catalog'], ensure_ascii=False)}\n\n"
        "【近期症状（供参考，注意避免诱发食物）】\n"
        f"{json.dumps(context['symptoms'], ensure_ascii=False)}\n\n"
        f"【需排除的食物 ID】 {json.dumps(list(exclude_food_ids or []), ensure_ascii=False)}\n"
        f"【近期身体状态】 {body_state or '无'}\n\n"
        "请严格按 system 指令的 JSON 结构输出食谱，至少包含 3 种食物，"
        "不要包含任何 red 食物，并遵守用量与组合负荷约束。"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _extract_json(text: Optional[str]) -> Optional[dict]:
    """从模型输出中健壮地抽取 JSON 对象。

    依次尝试：直接解析 → 剥离 ```json 围栏 → 截取首个 { 到最后一个 }（容忍截断）。
    全部失败返回 ``None``。
    """
    if not text:
        return None
    t = text.strip()

    # 处理 ```json ... ``` / ``` ... ``` 围栏
    fence = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL | re.IGNORECASE)
    if fence:
        t = fence.group(1).strip()

    # 直接解析
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass

    # 截取首个 { 到最后一个 }（容忍首尾多余字符 / 截断）
    first, last = t.find("{"), t.rfind("}")
    if first != -1 and last > first:
        try:
            return json.loads(t[first : last + 1])
        except json.JSONDecodeError:
            pass

    return None


def _parse_and_normalize(
    content: Optional[str],
    red_food_ids: set,
    name_to_id: Dict[str, int],
    body_state: Optional[str],
) -> Optional[Dict[str, Any]]:
    """解析模型输出并防御式清洗为 ``RecipeOut`` 兼容结构。

    解析失败 / 无有效条目 → 返回 ``None``（触发模板回退）。
    """
    recipe = _extract_json(content)
    if not isinstance(recipe, dict):
        return None

    raw_items = recipe.get("items") or []
    if not isinstance(raw_items, list) or not raw_items:
        return None

    items: List[Dict[str, Any]] = []
    for it in raw_items:
        if not isinstance(it, dict):
            continue
        # 名称：兼容 "name" 或个别模型用的 "food"
        name = it.get("name") or it.get("food")
        if not name or not str(name).strip():
            continue
        name = str(name).strip()

        # 食物 ID：优先用模型给的 id；缺失则按名称回解。
        food_id = it.get("food_id")
        if food_id is None:
            food_id = name_to_id.get(name)
        if isinstance(food_id, str) and food_id.isdigit():
            food_id = int(food_id)
        # 防御：硬性冲突（🔴）食物一律丢弃。
        if isinstance(food_id, int) and food_id in red_food_ids:
            continue

        # 安全等级归一
        safety = str(it.get("safety") or "green").strip().lower()
        if safety not in _VALID_SAFETY:
            safety = "green"

        # 用量取整，<=0 给一个安全默认下限
        try:
            amount = int(round(float(it.get("amount_g") or 0)))
        except (TypeError, ValueError):
            amount = 0
        if amount <= 0:
            amount = 30

        replaceable = it.get("replaceable_with") or []
        if not isinstance(replaceable, list):
            replaceable = []
        replaceable = [str(x) for x in replaceable]

        reason = it.get("reason")
        reason = str(reason) if reason else ""

        items.append(
            {
                "food_id": food_id,
                "name": name,
                "amount_g": amount,
                "safety": safety,
                "replaceable_with": replaceable,
                "reason": reason,
            }
        )

    if not items:
        return None

    return {
        "title": str(recipe.get("title") or "吾食个性化食谱（DeepSeek）"),
        "note": str(recipe.get("note") or body_state or ""),
        "items": items,
    }
