"""食物地图路由集成测试（T2 三色 + 三剂量）。"""

from __future__ import annotations

import pytest


async def _auth(client):
    await client.post(
        "/api/v1/auth/register",
        json={"nickname": "u", "phone": "13800000000", "password": "pw123456"},
    )
    r = await client.post(
        "/api/v1/auth/login", json={"phone": "13800000000", "password": "pw123456"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_map_returns_per_food_safety(client, seed_foods):
    headers = await _auth(client)
    r = await client.get("/api/v1/map", headers=headers)
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 18
    for it in items:
        assert it["level"] in ("green", "yellow", "red")
        assert "safe_g" in it and "caution_g" in it and "unsafe_g" in it
    names = [it["food"]["name"] for it in items]
    assert "洋葱" in names


@pytest.mark.asyncio
async def test_map_category_filter(client, seed_foods):
    headers = await _auth(client)
    r = await client.get("/api/v1/map?category=米饭", headers=headers)
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["food"]["name"] == "米饭(白)"


@pytest.mark.asyncio
async def test_map_requires_auth(client):
    r = await client.get("/api/v1/map")
    assert r.status_code == 401
