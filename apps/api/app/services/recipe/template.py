"""模板食谱生成（T2，纯规则，不调用外部 LLM）。

策略（与架构设计 §9.2 回退策略一致）：
1. 基础食材从 🟢 安全库抽取 ≥70%，按食物常用份量 / 安全剂量确定克数。
2. 探索性插入 1–2 种 🟡 食物，剂量取各自 ``safe_g × 70%``。
3. 每食材标注 safety 徽章、精确到克、给出 ``replaceable_with`` 可替换项与 reason。
4. 汇总 ``total_fodmap_load`` / ``total_gl``，并产出 ``burden_warning``。
5. ``generated_by='template'``（DeepSeek 在 T3 接入，本期不调用）。

说明：生成过程中会按需为食物建立 / 读取 ``ToleranceThreshold``（冷启动先验），
以保证 safety 等级与剂量一致，不产生副作用性破坏。
"""

from __future__ import annotations

import math
import uuid
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import Food
from app.services.burden import compute_burden
from app.services.safety import compute_safety
from app.services.tolerance.model import get_or_init_threshold
from app.services.tolerance.prior import is_high_fodmap as _is_high_fodmap

# 单餐基础食材数量
_BASE_ITEM_COUNT = 5
# 基础上至少的 🟢 占比
_GREEN_RATIO = 0.7
# 探索性插入的 🟡 数量上限
_EXPLORATORY_MAX = 2
# 单食材份量上下限（克）
_PORTION_MIN = 30.0
_PORTION_MAX = 150.0


async def _safe_g_of(session: AsyncSession, user_id: int, food_id: int) -> int:
    """获取某食物对用户的当前安全剂量（克）。"""
    threshold = await get_or_init_threshold(user_id, food_id, session)
    return threshold.safe_g


def _portion(food: Food, safe_g: int) -> int:
    """根据安全剂量给出单食材份量（克），限制在合理区间。"""
    amount = round(min(max(safe_g, _PORTION_MIN), _PORTION_MAX))
    return max(amount, 10)


async def _sort_by_safe_g(
    session: AsyncSession, user_id: int, items: List[Tuple[Food, str]], reverse: bool = False
) -> List[Tuple[Food, str]]:
    """按食物安全剂量降序排序候选列表。"""
    scored = []
    for food, level in items:
        safe_g = await _safe_g_of(session, user_id, food.id)
        scored.append((food, level, safe_g))
    scored.sort(key=lambda x: x[2], reverse=reverse)
    return [(f, lvl) for f, lvl, _ in scored]


async def generate_recipe(
    session: AsyncSession,
    user_id: int,
    target_weights: Optional[dict] = None,
    body_state: Optional[str] = None,
    exclude_food_ids: Optional[List[int]] = None,
) -> Dict[str, object]:
    """生成模板食谱（不调用 LLM）。

    Args:
        session: 异步数据库会话。
        user_id: 用户 ID。
        target_weights: 目标权重字典（如 ``{"gut_stability": 0.7, ...}``）。
        body_state: 身体状态备注（可选）。
        exclude_food_ids: 需排除的食物 ID 列表（可选）。

    Returns:
        符合共享 ``RecipeJSON`` 结构的字典，``generated_by='template'``。
    """
    exclude = set(exclude_food_ids or [])
    weights = target_weights or {
        "gut_stability": 0.7,
        "blood_sugar": 0.2,
        "fat_loss": 0.1,
    }

    foods = list(await session.scalars(select(Food)))
    candidates: List[Tuple[Food, str]] = []
    for food in foods:
        if food.id in exclude:
            continue
        safety = await compute_safety(session, user_id, food.id)
        candidates.append((food, str(safety.level)))

    green = [c for c in candidates if c[1] == "green"]
    yellow = [c for c in candidates if c[1] == "yellow"]

    green_sorted = await _sort_by_safe_g(session, user_id, green, reverse=True)
    yellow_sorted = await _sort_by_safe_g(session, user_id, yellow, reverse=True)

    # 基础食材仅从 🟢 安全库抽取；探索性插入仅用非高 FODMAP 的 🟡 食物
    # （高 FODMAP 食物在无诊断上下文时不应直接进入食谱，避免盲目引入风险食材）
    base = green_sorted[:_BASE_ITEM_COUNT]
    base_ids = {f.id for f, _ in base}
    exploratory = [
        c for c in yellow_sorted
        if c[0].id not in base_ids and not _is_high_fodmap(c[0])
    ][:_EXPLORATORY_MAX]

    items_plan: List[Tuple[Food, str, int]] = []
    for food, _lvl in base:
        safe_g = await _safe_g_of(session, user_id, food.id)
        items_plan.append((food, _lvl, _portion(food, safe_g)))
    for food, _lvl in exploratory:
        th = await get_or_init_threshold(user_id, food.id, session)
        amount = max(round(th.safe_g * 0.7), 10)
        items_plan.append((food, "yellow", amount))

    # 组装食谱项 + 组合负担输入 + 营养汇总
    recipe_items: List[Dict[str, object]] = []
    exploratory_inserts: List[str] = []
    food_amount_pairs: List[Tuple[Food, float]] = []
    nutrition = {"kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carb_g": 0.0}

    for food, level, amount in items_plan:
        # 可替换项：其它 🟢 食物（最多 3）
        replaceable = [f.name for f, _ in green_sorted if f.id != food.id][:3]
        if not replaceable:
            replaceable = [f.name for f, _ in yellow_sorted if f.id != food.id][:3]

        if level == "yellow":
            reason = "探索性插入（按安全阈值70%剂量）"
            exploratory_inserts.append(f"{food.name} {amount}g（按安全阈值70%）")
        else:
            reason = "低FODMAP安全食材，优先选用"

        recipe_items.append(
            {
                "food_id": food.id,
                "name": food.name,
                "food": food.name,
                "amount_g": float(amount),
                "safety": level.lower(),
                "replaceable_with": replaceable,
                "reason": reason,
            }
        )
        food_amount_pairs.append((food, float(amount)))

        factor = float(amount) / 100.0
        nut = food.nutrients or {}
        for key in ("kcal", "protein_g", "fat_g", "carb_g"):
            nutrition[key] += factor * float(nut.get(key, 0.0) or 0.0)

    burden = compute_burden(food_amount_pairs)
    burden_warning = "; ".join(burden.messages) if burden.messages else None

    if body_state:
        note = f"（身体状态：{body_state}）"
        title = f"吾食个性化食谱（模板）{note}"
    else:
        title = "吾食个性化食谱（模板）"

    recipe = {
        "recipe_id": f"tpl-{user_id}-{uuid.uuid4().hex[:8]}",
        "title": title,
        "note": body_state or "",
        "target_weights": weights,
        "items": recipe_items,
        "total_fodmap_load": float(burden.total_fodmap_load),
        "total_gl": float(burden.total_gl),
        "burden_warning": burden_warning,
        "steps": ["按剂量称取食材", "洗净切配", "适度烹调（少油少糖）", "按三色徽章摆盘"],
        "nutrition": {k: round(v, 1) for k, v in nutrition.items()},
        "exploratory_inserts": exploratory_inserts,
        "generated_by": "template",
    }
    return recipe
