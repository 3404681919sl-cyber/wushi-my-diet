"""安全工具：密码哈希（bcrypt）与 JWT 签发 / 校验。

- 密码：绝不以明文存储，统一经 passlib 的 bcrypt 方案哈希。
- JWT：使用 python-jose 基于 ``settings.JWT_SECRET`` 签发 HS256 access token，
  ``sub`` 声明存放用户 ID。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# 仅启用 bcrypt 方案；deprecated="auto" 便于未来平滑迁移
_pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希，返回可安全存储的哈希串。"""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与存储哈希是否匹配。"""
    if not hashed_password:
        return False
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str | int, expires_minutes: int | None = None) -> str:
    """签发 JWT access token，``sub`` 为用户 ID 字符串。"""
    expire_delta = timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire_at = datetime.now(timezone.utc) + expire_delta
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire_at}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """解码并返回 ``sub``（用户 ID 字符串）；无效 / 过期返回 ``None``。"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
    return payload.get("sub")
