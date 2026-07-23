"""三色安全评估（T2）：综合冲突与学习阈值给出 GREEN / YELLOW / RED。

规则优先级：
1. 命中高严重度冲突（FODMAP / histamine / glucose）→ RED；
2. 尚无个人观测（冷启动）→ YELLOW（建议微挑战）；
3. 95% 分位不安全剂量 < 10g → RED（高度敏感）；
4. 5% 分位安全剂量 ≥ 30g → GREEN；
5. 其余 → YELLOW。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import Food

from .conflict.engine import compute_conflicts
from .tolerance.model import get_threshold_values

# 安全 / 危险分位剂量阈值（克）
SAFE_GREEN_THRESHOLD = 30
UNSAFE_RED_THRESHOLD = 10


@dataclass
class SafetyResult:
    """三色安全评估结果。

    同时支持属性访问（``res.level``）与字典访问（``res["level"]``），
    以兼容调用方（``map.py`` 用字典访问，``recipe/template.py`` 用属性访问）。
    """

    level: str
    reason: str

    def __getitem__(self, key: str) -> Union[str, None]:
        """支持 ``res["level"]`` / ``res["reason"]`` 字典式访问。"""
        return getattr(self, key)


async def compute_safety(db: AsyncSession, user_id: int, food_id: int) -> SafetyResult:
    """评估某食物对某用户的三色安全等级。

    Args:
        db: 异步数据库会话。
        user_id: 用户 ID。
        food_id: 食物 ID。

    Returns:
        ``SafetyResult``，``level`` ∈ {green, yellow, red}，``reason`` 为解释。
    """
    food = await db.get(Food, food_id)
    if food is None:
        return SafetyResult(level="red", reason="食物不存在")

    conflicts = await compute_conflicts(db, user_id, food)
    # compute_conflicts 返回 dict 列表（含 hard/overridden），这里按 hard 判定高严重度冲突
    high_conflicts = [c for c in conflicts if c.get("hard")]
    if high_conflicts:
        detail = "; ".join(f"{c['condition_name']}({c['dimension']})" for c in high_conflicts)
        return SafetyResult(level="red", reason=f"与当前健康状况冲突：{detail}")

    tv = await get_threshold_values(user_id, food_id, db, persist=False)
    if tv["n_obs"] == 0:
        return SafetyResult(level="yellow", reason="冷启动：尚无个人数据，建议先做微挑战测试")

    if tv["unsafe_g"] < UNSAFE_RED_THRESHOLD:
        return SafetyResult(
            level="red",
            reason="高度敏感：极少剂量即可能不适（95% 分位不安全剂量 < 10g）",
        )

    if tv["safe_g"] >= SAFE_GREEN_THRESHOLD:
        return SafetyResult(level="green", reason="可放心食用（5% 分位安全剂量 ≥ 30g）")

    return SafetyResult(level="yellow", reason="适量谨慎食用（安全剂量偏低，建议从小量开始）")
