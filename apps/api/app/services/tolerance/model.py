"""阈值落库与增量更新编排（T2）。

对外提供：
- ``get_threshold_values``：取（或推导）某用户对某食物的阈值数值（可选落库）；
- ``get_or_init_threshold``：取或初始化阈值行（落库）；
- ``record_challenge_result``：用微挑战步骤结果重算并落库阈值；
- ``record_meal``：用餐日志 + 症状日志驱动阈值增量更新。
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge, ChallengeStep
from app.models.food import Food
from app.models.tolerance import ToleranceThreshold

from .prior import build_prior
from .update import conjugate_update, quantile_doses


async def get_threshold_values(
    user_id: int,
    food_id: int,
    db: AsyncSession,
    *,
    persist: bool = False,
) -> dict:
    """返回某用户对某食物的阈值数值（默认不写库）。

    若库中存在阈值行则直接返回；否则基于先验推导（``persist=True`` 时落库）。

    Returns:
        含 ``prior_mean / prior_var / post_mean / post_var / safe_g /
        caution_g / unsafe_g / n_obs`` 的字典。
    """
    th = await db.scalar(
        select(ToleranceThreshold).where(
            ToleranceThreshold.user_id == user_id,
            ToleranceThreshold.food_id == food_id,
        )
    )
    if th is not None:
        return {
            "prior_mean": th.prior_mean,
            "prior_var": th.prior_var,
            "post_mean": th.post_mean,
            "post_var": th.post_var,
            "safe_g": th.safe_g,
            "caution_g": th.caution_g,
            "unsafe_g": th.unsafe_g,
            "n_obs": th.n_obs,
        }

    food = await db.get(Food, food_id)
    if food is None:
        return {
            "prior_mean": 0.0,
            "prior_var": 1.0,
            "post_mean": 0.0,
            "post_var": 1.0,
            "safe_g": 0,
            "caution_g": 0,
            "unsafe_g": 0,
            "n_obs": 0,
        }

    mean, var = build_prior(food)
    safe, caution, unsafe = quantile_doses(mean, var)
    if persist:
        th = ToleranceThreshold(
            user_id=user_id,
            food_id=food_id,
            prior_mean=mean,
            prior_var=var,
            post_mean=mean,
            post_var=var,
            safe_g=safe,
            caution_g=caution,
            unsafe_g=unsafe,
            n_obs=0,
        )
        db.add(th)
        await db.commit()
        await db.refresh(th)
    return {
        "prior_mean": mean,
        "prior_var": var,
        "post_mean": mean,
        "post_var": var,
        "safe_g": safe,
        "caution_g": caution,
        "unsafe_g": unsafe,
        "n_obs": 0,
    }


async def get_or_init_threshold(
    user_id: int,
    food_id: int,
    db: AsyncSession,
) -> ToleranceThreshold:
    """取或初始化某用户对某食物的阈值行（落库）。"""
    existing = await db.scalar(
        select(ToleranceThreshold).where(
            ToleranceThreshold.user_id == user_id,
            ToleranceThreshold.food_id == food_id,
        )
    )
    if existing is not None:
        return existing

    food = await db.get(Food, food_id)
    mean, var = build_prior(food)
    safe, caution, unsafe = quantile_doses(mean, var)
    th = ToleranceThreshold(
        user_id=user_id,
        food_id=food_id,
        prior_mean=mean,
        prior_var=var,
        post_mean=mean,
        post_var=var,
        safe_g=safe,
        caution_g=caution,
        unsafe_g=unsafe,
        n_obs=0,
    )
    db.add(th)
    await db.commit()
    await db.refresh(th)
    return th


async def _upsert_threshold(
    *,
    user_id: int,
    food_id: int,
    mean0: float,
    var0: float,
    mean: float,
    var: float,
    n_obs: int,
    db: AsyncSession,
    commit: bool = True,
) -> ToleranceThreshold:
    """创建或更新某用户对某食物的阈值行。

    Args:
        commit: 是否立即提交。`record_challenge_result` 等调用方需要落库，
            传 ``True``；`record_meal` 由调用方统一提交，传 ``False``（仅 flush）。
    """
    safe, caution, unsafe = quantile_doses(mean, var)
    th = await db.scalar(
        select(ToleranceThreshold).where(
            ToleranceThreshold.user_id == user_id,
            ToleranceThreshold.food_id == food_id,
        )
    )
    if th is None:
        th = ToleranceThreshold(user_id=user_id, food_id=food_id)
        db.add(th)
    th.prior_mean = mean0
    th.prior_var = var0
    th.post_mean = mean
    th.post_var = var
    th.safe_g = safe
    th.caution_g = caution
    th.unsafe_g = unsafe
    th.n_obs = n_obs
    if commit:
        await db.commit()
        await db.refresh(th)
    else:
        await db.flush()
    return th


async def record_challenge_result(
    user_id: int,
    food_id: int,
    db: AsyncSession,
) -> ToleranceThreshold:
    """用某用户某食物的全部微挑战步骤结果重算并落库阈值。

    对每个已记录结果的步骤：``ok`` → severity 0，``reacted`` → severity 1。
    从先验出发，对所有观测做闭式共轭更新（幂等、可重放）。
    """
    food = await db.get(Food, food_id)
    mean0, var0 = build_prior(food)

    steps = list(
        await db.scalars(
            select(ChallengeStep)
            .join(Challenge, ChallengeStep.challenge_id == Challenge.id)
            .where(
                Challenge.user_id == user_id,
                Challenge.food_id == food_id,
                ChallengeStep.result.isnot(None),
            )
        )
    )

    observations = [
        (max(step.dose_g, 0.5), 0 if step.result == "ok" else 1) for step in steps
    ]
    if observations:
        res = conjugate_update(mean0, var0, observations)
        mean, var, n_obs = res.mean, res.var, res.n_obs
    else:
        mean, var, n_obs = mean0, var0, 0

    return await _upsert_threshold(
        user_id=user_id,
        food_id=food_id,
        mean0=mean0,
        var0=var0,
        mean=mean,
        var=var,
        n_obs=n_obs,
        db=db,
    )


async def record_meal(
    session: AsyncSession,
    user_id: int,
    meal_log_id: int,
    items: list[tuple[int, float]],
    symptom_by_food: dict[int, int],
) -> list[ToleranceThreshold]:
    """用餐日志 + 症状日志驱动阈值增量更新。

    对每个食物条目 ``(food_id, amount_g)``，结合 ``symptom_by_food`` 中该食物的
    反应严重度（0~10，默认 0=无症状）构造区间删失观测，做闭式共轭更新；
    返回每个食物更新后的 ``ToleranceThreshold`` 行（长度 = 食物数）。

    Args:
        session: 异步数据库会话。
        user_id: 用户 ID。
        meal_log_id: 餐日志 ID（预留，便于将来与 ``MealLog`` 关联审计）。
        items: 餐条目列表，元素为 ``(food_id, amount_g)``。
        symptom_by_food: ``{food_id: severity}``，反应严重度 0~10。

    Returns:
        按 ``items`` 顺序返回更新后的 ``ToleranceThreshold`` 列表。
        提交由调用方负责（本函数仅 add/flush）。
    """
    updated: list[ToleranceThreshold] = []
    for food_id, amount_g in items:
        food = await session.get(Food, food_id)
        mean0, var0 = build_prior(food)
        severity = int(symptom_by_food.get(food_id, 0))
        observations: list[tuple[float, int]] = [(max(float(amount_g), 0.5), severity)]
        res = conjugate_update(mean0, var0, observations)
        th = await _upsert_threshold(
            user_id=user_id,
            food_id=food_id,
            mean0=mean0,
            var0=var0,
            mean=res.mean,
            var=res.var,
            n_obs=res.n_obs,
            db=session,
            commit=False,
        )
        updated.append(th)
    return updated
