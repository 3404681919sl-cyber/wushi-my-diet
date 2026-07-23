"""pytest 全局夹具。

- 测试前将 ``DATABASE_URL`` 设为 SQLite（本地无 PostgreSQL 时的验证用库），
  确保 ``app.db.base`` 在导入时使用 SQLite 引擎。
- 每个测试前重建全部表，保证用例隔离。
- 提供异步 HTTP 客户端（httpx + ASGITransport）直接驱动 FastAPI 应用。
"""

from __future__ import annotations

import os

# 必须在导入 app 之前设置测试用数据库 URL
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.base import Base, engine
import app.models  # noqa: F401  注册全部模型


@pytest_asyncio.fixture(autouse=True)
async def _prepare_database():
    """每个测试前重建全部表，测试后清理。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """异步测试客户端（直接驱动 ASGI 应用，不占用端口）。"""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def seeded_client(client: AsyncClient) -> AsyncClient:
    """在测试库中预置 A6 内置食物后返回客户端。"""
    from app.db.base import AsyncSessionLocal
    from app.db.seed import seed_preset_foods

    async with AsyncSessionLocal() as session:
        await seed_preset_foods(session)
    yield client


@pytest_asyncio.fixture
async def seed_foods():
    """向测试库写入 A6 预设食物（供 challenge / recipe / map 用例使用）。"""
    from app.db.base import AsyncSessionLocal
    from app.db.seed import seed_preset_foods

    async with AsyncSessionLocal() as session:
        await seed_preset_foods(session)
