"""依赖注入：数据库会话与当前登录用户。

- ``get_db``：每个请求一个异步会话，请求结束自动关闭。
- ``get_current_user``：从 ``Authorization: Bearer <token>`` 解析 JWT，加载并返回当前用户；
  凭证缺失 / 无效 / 用户不存在时返回 401。
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User

# tokenUrl 指向登录端点，供 OpenAPI 文档的「Authorize」按钮使用
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """提供请求级异步数据库会话（复用 ``db.session.get_session``）。"""
    async for session in get_session():
        yield session


async def get_current_user(
    token: str | None = Depends(_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """解析 JWT 并返回当前登录用户，失败抛出 401。"""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效或未提供认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise unauthorized

    subject = decode_access_token(token)
    if subject is None:
        raise unauthorized

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise unauthorized

    user = await db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user
