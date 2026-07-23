"""画像路由：GET / PUT /api/v1/profile。

返回 / 更新当前用户的画像（``target_weights``），并附带其录入的
健康状况（conditions）与自定义症状词典（symptom_defs）。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.condition import Condition
from app.models.profile import Profile
from app.models.symptom import SymptomDef
from app.models.user import User
from app.schemas.profile import (
    ConditionOut,
    ProfileOut,
    ProfileUpdate,
    SymptomDefOut,
)

router = APIRouter(prefix="/profile", tags=["profile"])


async def _build_profile_out(db: AsyncSession, profile: Profile) -> ProfileOut:
    """组装 ProfileOut（含 conditions 与 symptom_defs 列表）。"""
    conditions = list(
        await db.scalars(select(Condition).where(Condition.user_id == profile.user_id))
    )
    symptom_defs = list(
        await db.scalars(select(SymptomDef).where(SymptomDef.user_id == profile.user_id))
    )
    data = ProfileOut.model_validate(profile)
    data.conditions = [ConditionOut.model_validate(c) for c in conditions]
    data.symptom_defs = [SymptomDefOut.model_validate(s) for s in symptom_defs]
    return data


async def _get_or_create_profile(db: AsyncSession, user: User) -> Profile:
    """获取用户画像，不存在则创建默认画像。"""
    profile = await db.scalar(select(Profile).where(Profile.user_id == user.id))
    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.get("", response_model=ProfileOut)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ProfileOut:
    """获取当前用户画像（含状况与症状词典）。"""
    profile = await _get_or_create_profile(db, current_user)
    return await _build_profile_out(db, profile)


@router.put("", response_model=ProfileOut)
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ProfileOut:
    """更新当前用户画像（目前支持更新目标权重 ``target_weights``）。"""
    profile = await _get_or_create_profile(db, current_user)
    if payload.target_weights is not None:
        profile.target_weights = payload.target_weights
        await db.commit()
        await db.refresh(profile)
    return await _build_profile_out(db, profile)
