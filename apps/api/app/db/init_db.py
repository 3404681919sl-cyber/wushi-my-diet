"""数据库初始化脚本（开发 / 测试兜底）。

优先使用 Alembic 迁移（``alembic upgrade head``）管理 schema；
本脚本作为无 Docker / 快速验证的兜底：直接 ``create_all`` 建表并写入 A6 预设食物。

用法：``python -m app.db.init_db``
"""

from __future__ import annotations

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import Base, engine
from app.db.seed import PRESET_FOODS, seed_preset_foods
import app.models  # noqa: F401  确保模型注册到 Base.metadata


async def init_db() -> None:
    """建表并种子化预设食物。"""
    # 1) 创建全部表（若已存在则跳过）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2) 验证连接
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    # 3) 种子化 A6 预设食物
    async with AsyncSession(engine) as session:
        added = await seed_preset_foods(session)

    print(f"[init_db] 数据库初始化完成：DATABASE_URL={settings.DATABASE_URL}")
    print(f"[init_db] 新增预设食物 {added} 条（预设共 {len(PRESET_FOODS)} 种）")


def _main() -> None:
    asyncio.run(init_db())


if __name__ == "__main__":
    _main()
