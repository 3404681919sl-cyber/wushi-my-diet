"""鉴权相关 Pydantic 模型（请求 / 响应）。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    """注册请求：手机号 + 密码 + 昵称（产品决策：手机号为主标识，不做邮箱）。

    注：本期短信验证码（SMS）暂未接入，使用「手机号 + 密码」直接注册即可；
    未来在此预留验证码校验点（如增加 sms_code 字段，注册前校验）。
    """

    phone: str = Field(
        ...,
        min_length=11,
        max_length=20,
        pattern=r"^1[3-9]\d{9}$",
        description="手机号（登录名，中国大陆 11 位）",
    )
    password: str = Field(..., min_length=6, max_length=128, description="密码（至少 6 位）")
    nickname: str = Field(default="", max_length=64, description="昵称")


class UserLogin(BaseModel):
    """登录请求：手机号 + 密码。"""

    phone: str = Field(
        ...,
        min_length=11,
        max_length=20,
        pattern=r"^1[3-9]\d{9}$",
        description="手机号",
    )
    password: str = Field(..., description="密码")


class WechatLoginRequest(BaseModel):
    """微信登录请求（预留）：小程序 wx.login 得到的 code。"""

    code: str = Field(..., description="wx.login 返回的临时登录 code")


class Token(BaseModel):
    """登录成功返回的令牌。"""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="令牌类型")


class UserOut(BaseModel):
    """用户公开信息（响应）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    phone: str | None = None
    email: str | None = None
    created_at: datetime
