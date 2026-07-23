"""微信登录预留模块（T1 仅占位，真实接线在后续阶段）。

未来 ``POST /api/v1/auth/wechat-login`` 将：
1. 用 ``code`` 调用微信 ``code2session`` 换取 ``openid`` / ``unionid``；
2. 在 ``User`` 表 upsert（按 ``wechat_union_id`` 唯一）；
3. 确保该用户拥有默认 ``Profile``；
4. 签发 JWT 返回。

本期路由返回 501，本模块提供可复用的 ``code2session`` 骨架（尚未启用）。
"""

from __future__ import annotations

import httpx

from app.core.config import settings

WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


async def code2session(code: str) -> dict:
    """调用微信 jscode2session 换取 openid / unionid。

    需在 ``.env`` 配置 ``WECHAT_APPID`` 与 ``WECHAT_SECRET``。
    当前为预留实现，未在生产启用。
    """
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(WECHAT_CODE2SESSION_URL, params=params)
        resp.raise_for_status()
        return resp.json()
