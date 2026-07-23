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
async def test_recipe_template_generated(client, seed_foods, monkeypatch):
    # 隔离环境变量：确保走模板回退路径（验证 T2 模板行为，不受 DEEPSEEK_API_KEY 影响）。
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

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
async def test_recipe_avoids_food(client, seed_foods, monkeypatch):
    # 隔离环境变量：确保走模板回退路径，验证模板的排食逻辑。
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

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


@pytest.mark.asyncio
async def test_recipe_fallback_without_key(client, seed_foods, monkeypatch):
    """未配置 DEEPSEEK_API_KEY 时，应静默回退模板，engine=='template'。"""
    # 确保环境变量缺省，真实 LLM 函数立即返回 None → 回退模板。
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    headers = await _auth(client)
    r = await client.post(
        "/api/v1/recipe",
        json={"goal": "gut_stability", "avoid_food_ids": []},
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["engine"] == "template"
    assert data["generated_by"] == "template"
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_recipe_llm_path(client, seed_foods, monkeypatch):
    """伪造 LLM 客户端返回固定 JSON，验证 engine=='llm' 且结构合法、无 🔴 冲突食物。"""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    async def fake_llm(*args, **kwargs):
        return {
            "title": "Mock LLM 食谱",
            "note": "测试用固定食谱",
            "items": [
                {
                    "food_id": 1,
                    "name": "胡萝卜",
                    "amount_g": 80,
                    "safety": "green",
                    "replaceable_with": ["菠菜"],
                    "reason": "低FODMAP安全食材",
                },
                {
                    "food_id": None,
                    "name": "鸡蛋",
                    "amount_g": 50,
                    "safety": "yellow",
                    "replaceable_with": [],
                    "reason": "探索性小剂量",
                },
            ],
        }

    # 在路由命名空间替换，使其绕过真实网络调用。
    monkeypatch.setattr("app.api.v1.recipe.generate_recipe_llm", fake_llm)

    headers = await _auth(client)
    r = await client.post(
        "/api/v1/recipe",
        json={"goal": "fat_loss", "avoid_food_ids": [], "body_state": "近期腹胀"},
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["engine"] == "llm"
    assert data["generated_by"] == "llm"
    assert len(data["items"]) > 0
    # 不应出现任何硬性冲突（🔴）食物
    assert all(it["safety"] != "red" for it in data["items"])
    # 结构合法：每项含必填字段
    for it in data["items"]:
        assert "name" in it and "amount_g" in it and "safety" in it
