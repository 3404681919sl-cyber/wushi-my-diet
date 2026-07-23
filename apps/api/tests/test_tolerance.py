"""贝叶斯耐受内核测试：先验差异 / 无症状升·有症状降 / n_obs 累加 / 餐后批量更新。

覆盖验收门槛 #2 的核心性质，并复用 SQLite（见 conftest）验证闭式共轭更新。
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.models.food import Food
from app.services.tolerance import prior as prior_mod
from app.services.tolerance import update as update_mod
from app.services.tolerance.model import record_meal

API = "/api/v1"

_FODMAP_NONE = {
    "fructan": "none",
    "gos": "low",
    "lactose": "none",
    "fructose": "none",
    "sorbitol": "none",
    "mannitol": "none",
}


def _onion() -> Food:
    """高 FODMAP（fructan high）食物。"""
    return Food(
        name="洋葱",
        fodmap_category={
            "fructan": "high",
            "gos": "low",
            "lactose": "none",
            "fructose": "low",
            "sorbitol": "none",
            "mannitol": "none",
        },
        gi=15,
        gl_per_100g=1.0,
        histamine_level="low",
        nutrients={"kcal": 40, "protein_g": 1.1, "fat_g": 0.1, "carb_g": 9.3},
    )


def _chicken() -> Food:
    """低 FODMAP 高营养（蛋白 31g）食物。"""
    return Food(
        name="鸡肉",
        fodmap_category=dict(_FODMAP_NONE),
        gi=0,
        gl_per_100g=0.0,
        histamine_level="moderate",
        nutrients={"kcal": 165, "protein_g": 31.0, "fat_g": 3.6, "carb_g": 0.0},
    )


async def _auth(client: AsyncClient, phone: str = "13800000000", password: str = "pw123456") -> dict:
    """辅助：用手机号注册并登录，返回鉴权头。"""
    await client.post(
        f"{API}/auth/register",
        json={"phone": phone, "password": password, "nickname": "u"},
    )
    login = await client.post(f"{API}/auth/login", json={"phone": phone, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _user_id(client: AsyncClient, headers: dict) -> int:
    me = await client.get(f"{API}/auth/me", headers=headers)
    return me.json()["id"]


# ------------------------- 纯函数单测（无需 DB） -------------------------


def test_prior_high_vs_low_fodmap_mu() -> None:
    """高 FODMAP 先验均值应低于低 FODMAP 高营养。"""
    m_onion, _ = prior_mod.build_prior(_onion())
    m_chicken, _ = prior_mod.build_prior(_chicken())
    assert m_chicken > m_onion


def test_update_asymptomatic_raises_safe() -> None:
    """同食物 3 次无症状（高剂量）→ safe_g 升高。"""
    mean0, var0 = prior_mod.build_prior(_onion())
    safe0, _, _ = update_mod.quantile_doses(mean0, var0)
    res = update_mod.conjugate_update(
        mean0, var0, [(100.0, 0), (140.0, 0), (196.0, 0)]
    )
    safe1, _, _ = update_mod.quantile_doses(res.mean, res.var)
    assert safe1 > safe0


def test_update_symptomatic_lowers_safe() -> None:
    """同食物 3 次有症状（低剂量）→ safe_g 降低。"""
    mean0, var0 = prior_mod.build_prior(_onion())
    safe0, _, _ = update_mod.quantile_doses(mean0, var0)
    res = update_mod.conjugate_update(
        mean0, var0, [(5.0, 9), (7.0, 9), (10.0, 9)]
    )
    safe1, _, _ = update_mod.quantile_doses(res.mean, res.var)
    assert safe1 < safe0


# ------------------------- 路由 / 服务集成 -------------------------


async def test_challenge_asymptomatic_raises_safe(seeded_client: AsyncClient) -> None:
    """微挑战 3 步无症状（高剂量）→ n_obs 累加且 safe_g 单调不降、整体升高。"""
    headers = await _auth(seeded_client, "13800000201")
    async with AsyncSessionLocal() as s:
        chicken = (await s.scalars(select(Food).where(Food.name == "鸡肉"))).first()

    resp = await seeded_client.post(
        f"{API}/challenge",
        headers=headers,
        json={"food_id": chicken.id, "steps": [100, 140, 196]},
    )
    assert resp.status_code == 201
    cid = resp.json()["id"]

    prev = None
    first = None
    for i, dose in enumerate([100, 140, 196], start=1):
        r = await seeded_client.post(
            f"{API}/challenge/{cid}/step",
            headers=headers,
            json={"step_no": i, "dose_g": dose, "severity": 0},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["n_obs"] == i
        if i == 1:
            first = body["safe_g"]
        else:
            assert body["safe_g"] >= prev  # 单调不降
        prev = body["safe_g"]
    assert prev > first  # 整体升高


async def test_challenge_symptomatic_lowers_safe(seeded_client: AsyncClient) -> None:
    """微挑战 3 步有症状（低剂量）→ safe_g 低于冷启动先验。"""
    headers = await _auth(seeded_client, "13800000202")
    async with AsyncSessionLocal() as s:
        onion = (await s.scalars(select(Food).where(Food.name == "洋葱"))).first()

    resp = await seeded_client.post(
        f"{API}/challenge", headers=headers, json={"food_id": onion.id, "steps": [3, 4, 6]}
    )
    assert resp.status_code == 201
    cid = resp.json()["id"]

    final_safe = None
    for i, dose in enumerate([3, 4, 6], start=1):
        r = await seeded_client.post(
            f"{API}/challenge/{cid}/step",
            headers=headers,
            json={"step_no": i, "dose_g": dose, "severity": 10},
        )
        assert r.status_code == 200
        body = r.json()
        final_safe = body["safe_g"]
        # 每次有症状反应后，安全剂量不应高于冷启动先验
        prior_safe_step = int(round(update_mod.quantile_doses(*prior_mod.build_prior(_onion()))[0]))
        assert body["safe_g"] <= prior_safe_step

    # 冷启动先验 safe_g（洋葱高 FODMAP）
    prior_safe = int(round(update_mod.quantile_doses(*prior_mod.build_prior(_onion()))[0]))
    assert body["n_obs"] == 3
    assert final_safe < prior_safe


async def test_record_meal_batch_updates(seeded_client: AsyncClient) -> None:
    """餐后批量更新：鸡肉无症状（高剂量）升高、米饭有症状（低剂量）降低，n_obs 累加。"""
    headers = await _auth(seeded_client, "13800000203")
    uid = await _user_id(seeded_client, headers)
    async with AsyncSessionLocal() as s:
        chicken = (await s.scalars(select(Food).where(Food.name == "鸡肉"))).first()
        rice = (await s.scalars(select(Food).where(Food.name == "米饭(白)"))).first()

    async with AsyncSessionLocal() as s:
        updated = await record_meal(
            s,
            uid,
            0,
            [(chicken.id, 120.0), (rice.id, 10.0)],
            {rice.id: 8},
        )
        assert len(updated) == 2
        by_food = {t.food_id: t for t in updated}
        chicken_thr = by_food[chicken.id]
        rice_thr = by_food[rice.id]

    # 鸡肉：无症状高剂量 → 升高
    chicken_prior_safe = int(round(update_mod.quantile_doses(*prior_mod.build_prior(_chicken()))[0]))
    assert chicken_thr.n_obs >= 1
    assert chicken_thr.safe_g > chicken_prior_safe

    # 米饭：有症状低剂量 → 降低
    rice_prior_safe = int(round(update_mod.quantile_doses(*prior_mod.build_prior(rice))[0]))
    assert rice_thr.n_obs >= 1
    assert rice_thr.safe_g < rice_prior_safe
