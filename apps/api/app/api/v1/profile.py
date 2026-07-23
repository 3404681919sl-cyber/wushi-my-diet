"""画像路由：GET / PUT /api/v1/profile。

返回 / 更新当前用户的画像（``target_weights``），并附带其录入的
健康状况（conditions）与自定义症状词典（symptom_defs）。
T2 扩展：支持录入 / 查询状况与症状词典，并基于冲突引擎返回冲突标注。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.condition import Condition
from app.models.food import Food
from app.models.profile import Profile
from app.models.symptom import SymptomDef
from app.models.user import User
from app.schemas.profile import (
    ConditionCreate,
    ConditionOut,
    ProfileOut,
    ProfileUpdate,
    SymptomDefCreate,
    SymptomDefOut,
)
from app.services.conflict.engine import compute_conflicts

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


# ---------------------------------------------------------------------------
# 健康状况（conditions）
# ---------------------------------------------------------------------------


@router.post("/conditions", response_model=ConditionOut, status_code=status.HTTP_201_CREATED)
async def create_condition(
    payload: ConditionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ConditionOut:
    """录入一条健康状况（可触发冲突标注）。"""
    condition = Condition(user_id=current_user.id, **payload.model_dump())
    db.add(condition)
    await db.commit()
    await db.refresh(condition)
    return ConditionOut.model_validate(condition)


@router.get("/conditions", response_model=list[ConditionOut])
async def list_conditions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[ConditionOut]:
    """列出当前用户全部状况。"""
    conditions = list(
        await db.scalars(select(Condition).where(Condition.user_id == current_user.id))
    )
    return [ConditionOut.model_validate(c) for c in conditions]


@router.get("/conflicts")
async def list_conflicts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """计算所有食物与当前 active 状况的冲突标注（用于前端冲突区渲染）。

    返回冲突列表：``{food_id, food_name, source, dimension, is_hard, note}``。
    """
    foods = list(await db.scalars(select(Food).order_by(Food.id)))
    result: list[dict] = []
    for food in foods:
        conflicts = await compute_conflicts(db, current_user.id, food)
        for conflict in conflicts:
            result.append(
                {
                    "food_id": food.id,
                    "food_name": food.name,
                    "source": conflict["condition_name"],
                    "dimension": conflict["dimension"],
                    "is_hard": conflict["hard"],
                    "overridden": conflict.get("overridden", False),
                }
            )
    return result


# ---------------------------------------------------------------------------
# 自定义症状词典（symptom_defs）
# ---------------------------------------------------------------------------


@router.post("/symptoms", response_model=SymptomDefOut, status_code=status.HTTP_201_CREATED)
async def create_symptom(
    payload: SymptomDefCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> SymptomDefOut:
    """新增一条自定义症状词典。"""
    symptom = SymptomDef(user_id=current_user.id, **payload.model_dump())
    db.add(symptom)
    await db.commit()
    await db.refresh(symptom)
    return SymptomDefOut.model_validate(symptom)


@router.get("/symptoms", response_model=list[SymptomDefOut])
async def list_symptoms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[SymptomDefOut]:
    """列出当前用户全部症状词典。"""
    symptoms = list(
        await db.scalars(select(SymptomDef).where(SymptomDef.user_id == current_user.id))
    )
    return [SymptomDefOut.model_validate(s) for s in symptoms]
