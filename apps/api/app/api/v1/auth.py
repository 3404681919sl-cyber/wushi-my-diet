"""鉴权路由：注册 / 登录 / 当前用户 / 微信登录（预留）。

统一前缀：``/api/v1/auth``
- ``POST /register``：邮箱 + 密码 + 昵称注册（密码 bcrypt 哈希）
- ``POST /login``：签发 JWT access_token
- ``GET /me``：返回当前登录用户（依赖 ``get_current_user``）
- ``POST /wechat-login``：预留，本期返回 501（未来接 code2session）
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserOut, WechatLoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_session),
) -> User:
    """注册新用户（邮箱唯一，密码经 bcrypt 哈希后存储）。"""
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已注册",
        )

    user = User(
        nickname=payload.nickname,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_session),
) -> Token:
    """邮箱密码登录，成功返回 JWT access_token。"""
    user = await db.scalar(select(User).where(User.email == payload.email))
    # 统一返回 401，避免泄露邮箱是否存在
    if user is None or user.password_hash is None or not verify_password(
        payload.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    access_token = create_access_token(user.id)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
async def read_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """返回当前登录用户（需 Bearer Token）。"""
    return current_user


@router.post("/wechat-login", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def wechat_login(payload: WechatLoginRequest) -> None:
    """微信登录（预留，本期未实现）。

    未来实现：用 ``payload.code`` 调 ``app.core.wechat.code2session`` 换取
    openid / unionid，按 ``wechat_union_id`` upsert ``User``，确保默认 ``Profile``，
    再签发 JWT 返回。本期先返回 501 占位。
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="微信登录尚未实现：未来将通过 code2session 换取 openid/unionid 并绑定用户",
    )
