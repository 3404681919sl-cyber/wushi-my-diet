"""用户模型。

存储账号核心信息：昵称、邮箱（唯一、可空）、bcrypt 密码哈希（绝不存明文）、
微信 unionid（预留、唯一、可空）。与 Profile 为 1:1，与多张业务表为 1:*。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """系统用户。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[str] = mapped_column(String(64), default="", comment="昵称")
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True, comment="邮箱（登录名，唯一可空）"
    )
    # 密码哈希：bcrypt 哈希串，绝不以明文存储
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="bcrypt 密码哈希"
    )
    # 微信 unionid：预留，用于微信登录绑定
    wechat_union_id: Mapped[Optional[str]] = mapped_column(
        String(128), unique=True, nullable=True, index=True, comment="微信 unionid（预留）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )

    # ---------- 关系 ----------
    profile: Mapped[Optional["Profile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    conditions: Mapped[list["Condition"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    symptom_defs: Mapped[list["SymptomDef"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    symptom_logs: Mapped[list["SymptomLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    meal_logs: Mapped[list["MealLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    challenges: Mapped[list["Challenge"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    tolerance_thresholds: Mapped[list["ToleranceThreshold"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# 关系目标类在文件末尾导入，避免循环依赖（SQLAlchemy 通过字符串注解解析）
from app.models.condition import Condition  # noqa: E402
from app.models.symptom import SymptomDef, SymptomLog  # noqa: E402
from app.models.meal import MealLog  # noqa: E402
from app.models.challenge import Challenge  # noqa: E402
from app.models.tolerance import ToleranceThreshold  # noqa: E402
from app.models.profile import Profile  # noqa: E402
