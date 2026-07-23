"""异步数据库会话依赖（供路由 / 脚本复用）。"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """按请求提供一个异步会话，结束后自动关闭。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
