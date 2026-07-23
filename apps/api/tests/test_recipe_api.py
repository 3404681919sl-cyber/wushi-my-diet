"""食谱路由集成测试（T2 模板生成）。"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.models.food import Food


async def _auth(client):
    await client.post(
        "/api/v1/auth/register",
        json={"nickname": "u", "email": "r@example.com", "password": "pw123456"},
    )
    r = await client.post(
        "/api/v1/auth/login", json={"email": "r@example.com", "password": "pw123456"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_recipe_template_generated(client, seed_foods):
    headers = await _auth(client)
    r = await client.post(
        "/api/v1/recipe",
        json={"goal": "gut_stability", "avoid_food_ids": []},
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["generated_by"] == "template"
    assert len(data["items"]) > 0
    names = [it["name"] for it in data["items"]]
    # 高 FODMAP 的洋葱不应进入 top5 模板
    assert "洋葱" not in names


@pytest.mark.asyncio
async def test_recipe_avoids_food(client, seed_foods):
    headers = await _auth(client)
    async with AsyncSessionLocal() as s:
        egg = (await s.scalars(select(Food).where(Food.name == "鸡蛋"))).first()
        fid = egg.id
    r = await client.post(
        "/api/v1/recipe",
        json={"goal": "fat_loss", "avoid_food_ids": [fid]},
        headers=headers,
    )
    assert r.status_code == 200
    ids = [it["food_id"] for it in r.json()["items"]]
    assert fid not in ids


@pytest.mark.asyncio
async def test_recipe_requires_auth(client):
    r = await client.post("/api/v1/recipe", json={"goal": "gut_stability"})
    assert r.status_code == 401
