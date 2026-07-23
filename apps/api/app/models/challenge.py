"""微挑战与步骤模型（B2）。

- ``Challenge``：为某个「心爱禁忌」食物生成的渐进式剂量测试计划，关联 ``Food`` 与 ``status``。
- ``ChallengeStep``：计划中的单次剂量步骤（``step_no``、``dose_g``、反应结果 ``result``、记录时间）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Challenge(Base):
    """微挑战计划（针对某食物）。"""

    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="关联用户"
    )
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), index=True, comment="关联目标食物"
    )
    status: Mapped[str] = mapped_column(
        String(32), default="active", comment="状态：active / done / aborted"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )

    user: Mapped["User"] = relationship(back_populates="challenges")
    food: Mapped["Food"] = relationship(back_populates="challenges")
    steps: Mapped[list["ChallengeStep"]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )


class ChallengeStep(Base):
    """微挑战的单次剂量步骤。"""

    __tablename__ = "challenge_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id", ondelete="CASCADE"), index=True, comment="关联挑战"
    )
    step_no: Mapped[int] = mapped_column(Integer, default=1, comment="步骤序号")
    dose_g: Mapped[int] = mapped_column(Integer, default=0, comment="本次剂量（克）")
    # 结果：ok（无不适）/ reacted（出现反应）/ None（未记录）
    result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="反应结果")
    logged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="记录时间"
    )

    challenge: Mapped["Challenge"] = relationship(back_populates="steps")


from app.models.user import User  # noqa: E402
from app.models.food import Food  # noqa: E402
