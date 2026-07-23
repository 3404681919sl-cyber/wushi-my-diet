"""用户画像模型（1:1 关联 User）。

存储多目标权重 ``target_weights``（JSONB），默认
``{"gut_stability": 0.7, "blood_sugar": 0.2, "fat_loss": 0.1}``，
用于食谱生成时的目标加权（C1）。后续阶段会在此基础上扩展量表口径等字段。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONB


class Profile(Base):
    """用户画像（每位用户一条）。"""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        comment="关联用户（1:1）",
    )
    # 多目标权重：肠道稳定 / 平稳血糖 / 减脂（默认 0.7 / 0.2 / 0.1）
    target_weights: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {"gut_stability": 0.7, "blood_sugar": 0.2, "fat_loss": 0.1},
        comment="多目标权重（JSONB）",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    user: Mapped["User"] = relationship(back_populates="profile")


from app.models.user import User  # noqa: E402
