"""食物目录路由：GET /foods 返回 A6 预设食物目录（供前端食物图谱 / 选择使用）。

统一前缀：``/api/v1/foods``
- ``GET /``：返回全部食物（含 fodmap_category / gi / gl_per_100g / histamine_level 等），
  字段与前端 ``FoodOut`` 对齐，可独立作为「食物目录」数据源（安全评估仍走 /map）。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.food import Food
from app.models.user import User
from app.schemas.food import FoodOut

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("", response_model=list[FoodOut])
async def list_foods(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[Food]:
    """返回食物目录（系统预设 + 用户自建），按 id 升序。"""
    foods = list(await db.scalars(select(Food).order_by(Food.id)))
    return foods
