"""食物地图路由：每食物三色安全 + 三剂量（T2）。

统一前缀：``/api/v1/map``
- ``GET /``：返回全部（或按 category 过滤的）食物安全评估列表
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.food import Food
from app.models.user import User
from app.schemas.map import ConflictOut, FoodSafetyOut, MapOut
from app.services.conflict.engine import compute_conflicts
from app.services.safety import compute_safety
from app.services.tolerance.model import get_threshold_values

router = APIRouter(prefix="/map", tags=["map"])


@router.get("", response_model=MapOut)
async def get_map(
    category: Optional[str] = Query(default=None, description="食物名称子串过滤"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> MapOut:
    """返回当前用户视角下各食物的安全等级与三色剂量。"""
    stmt = select(Food)
    if category:
        stmt = stmt.where(Food.name.contains(category))
    foods = list(await db.scalars(stmt))

    items: list[FoodSafetyOut] = []
    for food in foods:
        safety = await compute_safety(db, current_user.id, food.id)
        tv = await get_threshold_values(current_user.id, food.id, db, persist=False)
        conflicts = await compute_conflicts(db, current_user.id, food)
        items.append(
            FoodSafetyOut(
                food=food,
                level=safety["level"],
                reason=safety["reason"],
                safe_g=tv["safe_g"],
                caution_g=tv["caution_g"],
                unsafe_g=tv["unsafe_g"],
                conflicts=[
                    ConflictOut(
                        dimension=c.get("dimension", ""),
                        condition_name=c.get("condition_name", ""),
                        food_attribute="",
                        severity="hard" if c.get("hard") else "soft",
                        message=f"{c.get('condition_name', '')} 冲突（{'已覆盖' if c.get('overridden') else '硬冲突'}）",
                    )
                    for c in conflicts
                ],
            )
        )
    return MapOut(items=items)
