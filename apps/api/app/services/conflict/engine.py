"""矛盾破解引擎：用户 active 状况与食物的逐维度冲突比对。

维度：
- ``fodmap``：食物某 FODMAP 维度为 ``high`` 且状况 ``fodmap_flags`` 标记该维度 → 硬冲突。
- ``glucose``：食物 ``gi ≥ 70`` 且状况 ``glucose_flag`` 为真 → 冲突（硬）。
- ``histamine``：食物 ``histamine_level == "high"`` 且状况 ``histamine_flag`` 为真 → 冲突（硬）。

覆盖（B6）预留：若状况 ``override_json`` 标记该食物允许
（``{"allowed_food_ids": [...]}`` 或 ``{"allowed_foods": ["名称", ...]}``），
则将该冲突降级为非硬冲突（``hard=False``），并附 ``overridden=True`` 标注。
"""

from __future__ import annotations

from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.condition import Condition

# FODMAP 触发所需的最低等级
_HIGH_LEVEL = "high"
_GI_THRESHOLD = 70.0


async def compute_conflicts(
    session: AsyncSession,
    user_id: int,
    food,
) -> List[Dict[str, object]]:
    """计算食物与用户所有 active 状况的冲突。

    Args:
        session: 异步数据库会话。
        user_id: 用户 ID。
        food: ``Food`` ORM 实例（或带 ``fodmap_category`` / ``gi`` /
            ``histamine_level`` / ``id`` / ``name`` 的对象）。

    Returns:
        冲突列表，元素为 ``{"condition_name", "dimension", "hard", "overridden"}``。
        仅包含实际触发的维度；无冲突时返回空列表。
    """
    conditions = list(
        await session.scalars(
            select(Condition).where(
                Condition.user_id == user_id, Condition.is_active.is_(True)
            )
        )
    )

    fodmap: dict = getattr(food, "fodmap_category", None) or {}
    gi = float(getattr(food, "gi", 0.0) or 0.0)
    histamine = getattr(food, "histamine_level", "unknown") or "unknown"
    food_id = getattr(food, "id", None)
    food_name = getattr(food, "name", None)

    conflicts: List[Dict[str, object]] = []

    for cond in conditions:
        flags: dict = cond.fodmap_flags or {}
        override: dict = getattr(cond, "override_json", None) or {}

        # 覆盖判定：该食物被显式允许
        allowed_ids = override.get("allowed_food_ids") or []
        allowed_names = override.get("allowed_foods") or []
        is_overridden = (food_id in allowed_ids) or (
            food_name is not None and food_name in allowed_names
        )

        # ---- FODMAP 维度 ----
        for dim, level in fodmap.items():
            if level == _HIGH_LEVEL and flags.get(dim):
                conflicts.append(
                    {
                        "condition_name": cond.name,
                        "dimension": "fodmap",
                        "hard": not is_overridden,
                        "overridden": is_overridden,
                    }
                )
                break  # 同一状况仅计一次 fodmap 冲突

        # ---- 血糖维度 ----
        if gi >= _GI_THRESHOLD and cond.glucose_flag:
            conflicts.append(
                {
                    "condition_name": cond.name,
                    "dimension": "glucose",
                    "hard": not is_overridden,
                    "overridden": is_overridden,
                }
            )

        # ---- 组胺维度 ----
        if histamine == _HIGH_LEVEL and cond.histamine_flag:
            conflicts.append(
                {
                    "condition_name": cond.name,
                    "dimension": "histamine",
                    "hard": not is_overridden,
                    "overridden": is_overridden,
                }
            )

    return conflicts
