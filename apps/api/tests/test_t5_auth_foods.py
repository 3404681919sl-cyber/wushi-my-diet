"""T5 新增能力测试：phone 登录体系 + GET /api/v1/foods + recipe LLM 12s 截止回退。

仅改动测试代码，业务源码不在本文件范围内。
覆盖：
- phone 注册返回 201、email 为 null、无密码明文
- 重复手机号注册冲突（409）
- 错误密码 / 未注册手机号登录拒绝（401）
- GET /api/v1/foods 需鉴权（401）/ 带 token 返回非空列表（200）
- recipe 路由在 LLM 挂死时按截止（默认 12s，测试降到 2s）静默回退模板，不再卡死
"""

from __future__ import annotations

import asyncio
import time

from httpx import AsyncClient

API = "/api/v1"


async def _auth(
    client: AsyncClient, phone: str = "13800000000", password: str = "pw123456"
) -> dict:
    """辅助：用手机号注册并登录，返回鉴权头。"""
    reg = await client.post(
        f"{API}/auth/register",
        json={"phone": phone, "password": password, "nickname": "小易"},
    )
    assert reg.status_code == 201, reg.text
    login = await client.post(f"{API}/auth/login", json={"phone": phone, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def test_phone_register_201(client: AsyncClient) -> None:
    """用手机号注册 → 201，响应含 phone、email 为 null、绝不含密码。"""
    resp = await client.post(
        f"{API}/auth/register",
        json={"phone": "13800000000", "password": "pw123456", "nickname": "小易"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["phone"] == "13800000000"
    assert body.get("email") is None
    assert "password" not in body
    assert "password_hash" not in body


async def test_duplicate_phone_conflict(client: AsyncClient) -> None:
    """同一手机号注册两次 → 第二次被拒（409）。"""
    payload = {"phone": "13800000000", "password": "pw123456", "nickname": "x"}
    first = await client.post(f"{API}/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post(f"{API}/auth/register", json=payload)
    assert second.status_code == 409


async def test_login_wrong_password_401(client: AsyncClient) -> None:
    """注册后密码错误登录 → 401。"""
    await client.post(
        f"{API}/auth/register",
        json={"phone": "13800000000", "password": "rightpass", "nickname": "c"},
    )
    bad = await client.post(
        f"{API}/auth/login", json={"phone": "13800000000", "password": "wrongpass"}
    )
    assert bad.status_code == 401


async def test_login_unregistered_phone_401(client: AsyncClient) -> None:
    """用从未注册的手机号登录 → 401。"""
    r = await client.post(
        f"{API}/auth/login", json={"phone": "13900000000", "password": "pw123456"}
    )
    assert r.status_code == 401


async def test_foods_requires_auth(client: AsyncClient) -> None:
    """GET /api/v1/foods 不带 token → 401。"""
    r = await client.get(f"{API}/foods")
    assert r.status_code == 401


async def test_foods_returns_list(seeded_client: AsyncClient) -> None:
    """带 token（已预置食物）→ 200 且列表非空。"""
    headers = await _auth(seeded_client)
    r = await seeded_client.get(f"{API}/foods", headers=headers)
    assert r.status_code == 200
    foods = r.json()
    assert isinstance(foods, list)
    assert len(foods) > 0


async def test_recipe_llm_deadline_fallback(
    client: AsyncClient, seed_foods, monkeypatch
) -> None:
    """验证 T5 修复：LLM 挂死时按截止（测试降到 2s）静默回退模板，不再卡 20s+。

    - setenv DEEPSEEK_API_KEY 让路由进入 LLM 分支；
    - 将 _LLM_DEADLINE 降到 2.0，证明 12s 截止生效；
    - 用挂死的 fake_llm（sleep 30s）模拟 LLM 无响应；
    - 断言：status==200、engine=='template'、耗时 < 5s。
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy")
    monkeypatch.setattr("app.api.v1.recipe._LLM_DEADLINE", 2.0)

    async def fake_llm(*a, **k):
        await asyncio.sleep(30)
        return None

    monkeypatch.setattr("app.api.v1.recipe.generate_recipe_llm", fake_llm)

    headers = await _auth(client)
    start = time.monotonic()
    r = await client.post(
        f"{API}/recipe",
        json={"goal": "gut_stability", "avoid_food_ids": []},
        headers=headers,
    )
    elapsed = time.monotonic() - start

    assert r.status_code == 200
    data = r.json()
    assert data["engine"] == "template"
    # 截止 2s + 模板生成，应远小于修复前的 20s+ 卡死。
    assert elapsed < 5
