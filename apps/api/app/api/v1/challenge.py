"""微挑战路由：创建 / 查询 / 记录步骤结果（T2）。

统一前缀：``/api/v1/challenge``
- ``POST /``：为某食物创建微挑战（自动生成剂量阶梯步骤）
- ``GET /``：列出当前用户微挑战
- ``GET /{id}``：单个微挑战详情
- ``POST /{id}/step``：记录某步骤反应结果，并触发阈值重算
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.challenge import Challenge, ChallengeStep
from app.models.food import Food
from app.models.user import User
from app.schemas.challenge import ChallengeCreate, ChallengeOut, ChallengeStepOut, ChallengeStepUpdate
from app.services.tolerance.model import (
    get_or_init_threshold,
    get_threshold_values,
    record_challenge_result,
)

router = APIRouter(prefix="/challenge", tags=["challenge"])

# 剂量阶梯由先验 safe_g 推导：起点 safe_g*0.5，每步 +40%，共 3 步（见 create_challenge）


async def _load_challenge_out(db: AsyncSession, challenge: Challenge) -> ChallengeOut:
    """组装微挑战响应（显式加载步骤与标量属性，避免异步惰性加载）。

    注意：直接 ``challenge.steps = [...]`` 会触发关系集合的旧值惰性读取，
    在 AsyncSession 中抛 ``MissingGreenlet``。此处改为按 id 重新 SELECT 并
    ``selectinload`` 步骤，使所有字段均为已加载状态，序列化时不再触发 IO。
    """
    loaded = (
        await db.scalars(
            select(Challenge)
            .where(Challenge.id == challenge.id)
            .options(selectinload(Challenge.steps))
        )
    ).first()
    out = ChallengeOut.model_validate(loaded)
    # 附加当前耐受阈值（随 record_step 重算），前端可直接展示三色剂量
    tv = await get_threshold_values(loaded.user_id, loaded.food_id, db, persist=False)
    out.n_obs = tv["n_obs"]
    out.safe_g = tv["safe_g"]
    out.caution_g = tv["caution_g"]
    out.unsafe_g = tv["unsafe_g"]
    return out


@router.post("", response_model=ChallengeOut, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    payload: ChallengeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ChallengeOut:
    """为某食物创建微挑战，自动生成剂量阶梯步骤。"""
    food = await db.get(Food, payload.food_id)
    if food is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="食物不存在")

    challenge = Challenge(user_id=current_user.id, food_id=payload.food_id)
    db.add(challenge)
    await db.flush()

    # 初始化阈值（写入先验），并据此推导剂量阶梯：起点 safe_g*0.5，每步 +40%，共 3 步
    th = await get_or_init_threshold(current_user.id, payload.food_id, db)
    start = max(5, round(th.safe_g * 0.5))
    ladder = [start]
    for _ in range(2):
        ladder.append(round(ladder[-1] * 1.4))

    for step_no, dose in enumerate(ladder, start=1):
        db.add(ChallengeStep(challenge_id=challenge.id, step_no=step_no, dose_g=dose))

    await db.commit()

    return await _load_challenge_out(db, challenge)


@router.get("", response_model=list[ChallengeOut])
async def list_challenges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[ChallengeOut]:
    """列出当前用户全部微挑战。"""
    rows = list(
        await db.scalars(select(Challenge).where(Challenge.user_id == current_user.id))
    )
    return [await _load_challenge_out(db, c) for c in rows]


@router.get("/{challenge_id}", response_model=ChallengeOut)
async def get_challenge(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ChallengeOut:
    """获取单个微挑战详情。"""
    challenge = await db.get(Challenge, challenge_id)
    if challenge is None or challenge.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="微挑战不存在")
    return await _load_challenge_out(db, challenge)


@router.post("/{challenge_id}/step", response_model=ChallengeOut)
async def record_step(
    challenge_id: int,
    payload: ChallengeStepUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ChallengeOut:
    """记录某步骤反应结果，并触发贝叶斯阈值重算。"""
    challenge = await db.get(Challenge, challenge_id)
    if challenge is None or challenge.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="微挑战不存在")

    step = await db.scalar(
        select(ChallengeStep).where(
            ChallengeStep.challenge_id == challenge_id,
            ChallengeStep.step_no == payload.step_no,
        )
    )
    if step is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"步骤 {payload.step_no} 不存在",
        )

    step.severity = payload.severity
    step.result = "reacted" if payload.severity > 0 else "ok"
    await db.commit()

    # 重算并落库该用户对该食物的耐受阈值
    await record_challenge_result(current_user.id, challenge.food_id, db)
    return await _load_challenge_out(db, challenge)
