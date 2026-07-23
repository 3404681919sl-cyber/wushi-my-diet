"""食物库模型（含 A6 预设数据）。

``fodmap_category``（JSONB，六类 FODMAP 等级）、``gi``（升糖指数）、``gl_per_100g``（每 100g
血糖负荷）、``histamine_level``（组胺等级）、``nutrients``（JSONB 基础营养素）。
``is_preset`` 标记系统内置（冷启动先验知识库）。
"""

from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONB


class Food(Base):
    """食物（系统预设 + 用户可扩展）。"""

    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True, comment="食物名称")
    # FODMAP 六类等级，如 {"fructan": "high", "lactose": "low", ...}
    fodmap_category: Mapped[dict] = mapped_column(
        JSONB, default=dict, comment="FODMAP 六类等级（JSONB）"
    )
    gi: Mapped[float] = mapped_column(Float, default=0.0, comment="升糖指数 GI")
    gl_per_100g: Mapped[float] = mapped_column(Float, default=0.0, comment="每 100g 血糖负荷 GL")
    histamine_level: Mapped[str] = mapped_column(
        String(32), default="unknown", comment="组胺等级：low / moderate / high / unknown"
    )
    nutrients: Mapped[dict] = mapped_column(JSONB, default=dict, comment="基础营养素（JSONB）")
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否系统预设")

    meal_items: Mapped[list["MealItem"]] = relationship(back_populates="food")
    challenges: Mapped[list["Challenge"]] = relationship(back_populates="food")
    tolerance_thresholds: Mapped[list["ToleranceThreshold"]] = relationship(back_populates="food")
