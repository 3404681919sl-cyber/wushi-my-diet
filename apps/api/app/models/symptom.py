"""症状词典与症状日志模型。

- ``SymptomDef``：自定义症状词典（A3），如腹胀 / 腹痛 / 肠鸣，``scale_max`` 设严重度量表上限，
  ``is_custom`` 区分内置与用户自定义。
- ``SymptomLog``：某次餐后 / 自发症状记录，关联 ``SymptomDef`` 与严重度 ``severity``。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SymptomDef(Base):
    """症状词典条目（用户维度）。"""

    __tablename__ = "symptom_defs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="关联用户"
    )
    name: Mapped[str] = mapped_column(String(128), comment="症状名称（如腹胀）")
    scale_max: Mapped[int] = mapped_column(Integer, default=10, comment="严重度量表上限（默认 10）")
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否用户自定义")

    user: Mapped["User"] = relationship(back_populates="symptom_defs")
    logs: Mapped[list["SymptomLog"]] = relationship(
        back_populates="symptom_def", cascade="all, delete-orphan"
    )


class SymptomLog(Base):
    """症状日志（一次记录）。"""

    __tablename__ = "symptom_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="关联用户"
    )
    symptom_def_id: Mapped[int] = mapped_column(
        ForeignKey("symptom_defs.id", ondelete="CASCADE"), index=True, comment="关联症状词典"
    )
    severity: Mapped[int] = mapped_column(Integer, default=0, comment="严重度（0 ~ scale_max）")
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="记录时间"
    )

    user: Mapped["User"] = relationship(back_populates="symptom_logs")
    symptom_def: Mapped["SymptomDef"] = relationship(back_populates="logs")


from app.models.user import User  # noqa: E402
