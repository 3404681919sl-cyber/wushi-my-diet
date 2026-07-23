"""微挑战 / 冲突 / 三色 API 与引擎测试（T2）。

覆盖：建计划 → 步骤写回 → 后验更新、冲突引擎（洋葱+IBS 硬冲突 / 米饭无）、三色（红/黄/绿）。
冲突引擎返回 dict 列表，断言用键访问（``c["dimension"]`` / ``c["hard"]``）。
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.models.condition import Condition
from app.models.food import Food
from app.models.tolerance import ToleranceThreshold
from app.services.conflict.engine import compute_conflicts
from app.services.safety import compute_safety

API = "/api/v1"


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


async def _food_id(name: str) -> int:
    async with AsyncSessionLocal() as s:
        f = (await s.scalars(select(Food).where(Food.name == name))).first()
        return f.id


async def _insert(db, obj) -> None:
    db.add(obj)
    await db.commit()
    await db.refresh(obj)


async def test_create_challenge_plan(seeded_client: AsyncClient) -> None:
    """建计划：默认 3 步、剂量按 +40% 递增。"""
    headers = await _auth(seeded_client, "13800000101")
    fid = await _food_id("鸡肉")
    resp = await seeded_client.post(f"{API}/challenge", headers=headers, json={"food_id": fid})
    assert resp.status_code == 201
    body = resp.json()
    assert body["food_id"] == fid
    assert len(body["steps"]) == 3
    doses = [st["dose_g"] for st in body["steps"]]
    assert doses == sorted(doses)
    # 未记录反应时 severity 为 None
    assert all(st["severity"] is None for st in body["steps"])


async def test_challenge_get_and_list(seeded_client: AsyncClient) -> None:
    """GET 单个与列表均可返回已建计划。"""
    headers = await _auth(seeded_client, "13800000102")
    fid = await _food_id("洋葱")
    created = await seeded_client.post(f"{API}/challenge", headers=headers, json={"food_id": fid})
    cid = created.json()["id"]

    got = await seeded_client.get(f"{API}/challenge/{cid}", headers=headers)
    assert got.status_code == 200
    assert got.json()["id"] == cid

    lst = await seeded_client.get(f"{API}/challenge", headers=headers)
    assert lst.status_code == 200
    assert any(c["id"] == cid for c in lst.json())


async def test_record_step_updates_threshold(seeded_client: AsyncClient) -> None:
    """记录一步（有症状）→ 阈值落库，n_obs 累加为 1。"""
    headers = await _auth(seeded_client, "13800000103")
    fid = await _food_id("洋葱")
    created = await seeded_client.post(f"{API}/challenge", headers=headers, json={"food_id": fid})
    body0 = created.json()
    cid = body0["id"]
    step_no = body0["steps"][0]["step_no"]

    r = await seeded_client.post(
        f"{API}/challenge/{cid}/step",
        headers=headers,
        json={"step_no": step_no, "dose_g": 3, "severity": 10},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["n_obs"] == 1
    assert body["safe_g"] > 0
    assert body["caution_g"] >= body["safe_g"]
    assert body["unsafe_g"] >= body["caution_g"]


async def test_conflict_onion_ibs_hard_and_rice_none(seeded_client: AsyncClient) -> None:
    """洋葱 + IBS(fructan) → FODMAP 硬冲突；米饭 + 同状况 → 无冲突。"""
    headers = await _auth(seeded_client, "13800000104")
    uid = await _user_id(seeded_client, headers)
    onion_id = await _food_id("洋葱")
    rice_id = await _food_id("米饭(白)")
    async with AsyncSessionLocal() as s:
        await _insert(
            s,
            Condition(
                user_id=uid,
                name="IBS-D",
                fodmap_flags={"fructan": True},
                glucose_flag=False,
                histamine_flag=False,
                is_active=True,
            ),
        )
        onion = (await s.scalars(select(Food).where(Food.id == onion_id))).first()
        rice = (await s.scalars(select(Food).where(Food.id == rice_id))).first()
        c_onion = await compute_conflicts(s, uid, onion)
        c_rice = await compute_conflicts(s, uid, rice)
    assert any(c["dimension"] == "fodmap" and c["hard"] for c in c_onion)
    assert c_rice == []


async def test_safety_red_for_hard_conflict(seeded_client: AsyncClient) -> None:
    """硬冲突且 n_obs<2 → 🔴。"""
    headers = await _auth(seeded_client, "13800000105")
    uid = await _user_id(seeded_client, headers)
    onion_id = await _food_id("洋葱")
    async with AsyncSessionLocal() as s:
        await _insert(
            s,
            Condition(
                user_id=uid,
                name="IBS-D",
                fodmap_flags={"fructan": True},
                glucose_flag=False,
                histamine_flag=False,
                is_active=True,
            ),
        )
        res = await compute_safety(s, uid, onion_id)
    assert res.level == "red"


async def test_safety_yellow_for_low_safe(seeded_client: AsyncClient) -> None:
    """无硬冲突但安全剂量偏低 → 🟡。"""
    headers = await _auth(seeded_client, "13800000106")
    uid = await _user_id(seeded_client, headers)
    rice_id = await _food_id("米饭(白)")
    async with AsyncSessionLocal() as s:
        await _insert(
            s,
            Condition(
                user_id=uid,
                name="IBS-D",
                fodmap_flags={"fructan": True},
                glucose_flag=False,
                histamine_flag=False,
                is_active=True,
            ),
        )
        res = await compute_safety(s, uid, rice_id)
    assert res.level == "yellow"


async def test_safety_green_for_sufficient_data(seeded_client: AsyncClient) -> None:
    """无硬冲突且 safe_g ≥ 常用份量、n_obs≥2 → 🟢。"""
    headers = await _auth(seeded_client, "13800000107")
    uid = await _user_id(seeded_client, headers)
    chicken_id = await _food_id("鸡肉")
    async with AsyncSessionLocal() as s:
        await _insert(
            s,
            ToleranceThreshold(
                user_id=uid,
                food_id=chicken_id,
                prior_mean=4.3,
                prior_var=0.25,
                post_mean=4.7,
                post_var=0.04,
                safe_g=120,
                caution_g=150,
                unsafe_g=200,
                n_obs=3,
            ),
        )
        res = await compute_safety(s, uid, chicken_id)
    assert res.level == "green"
