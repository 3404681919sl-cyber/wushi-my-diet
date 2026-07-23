"""餐日志与餐条目模型。

- ``MealLog``：一次用餐记录，含 ``logged_at`` 与备注。
- ``MealItem``：该餐中的单项食物，关联 ``Food`` 与摄入量 ``amount_g``（克）。
  作为贝叶斯模型（B4）与组合负担（B3）的输入。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MealLog(Base):
    """餐日志（一次用餐）。"""

    __tablename__ = "meal_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="关联用户"
    )
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="用餐时间"
    )
    note: Mapped[str] = mapped_column(String(512), default="", comment="备注")

    user: Mapped["User"] = relationship(back_populates="meal_logs")
    items: Mapped[list["MealItem"]] = relationship(
        back_populates="meal_log", cascade="all, delete-orphan"
    )


class MealItem(Base):
    """餐条目（餐中的单项食物）。"""

    __tablename__ = "meal_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    meal_log_id: Mapped[int] = mapped_column(
        ForeignKey("meal_logs.id", ondelete="CASCADE"), index=True, comment="关联餐日志"
    )
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), index=True, comment="关联食物"
    )
    amount_g: Mapped[float] = mapped_column(Float, default=0.0, comment="摄入量（克）")

    meal_log: Mapped["MealLog"] = relationship(back_populates="items")
    food: Mapped["Food"] = relationship(back_populates="meal_items")


from app.models.user import User  # noqa: E402
from app.models.food import Food  # noqa: E402
