"""贝叶斯个人耐受阈值模型（核心表）。

存储每用户对每食物的个性化安全剂量后验：``prior_mean/prior_var``（log 空间先验）、
``post_mean/post_var``（上次后验）、``safe_g/caution_g/unsafe_g``（三色分位剂量）、
``n_obs``（观测数）、``updated_at``。由 ``services/tolerance``（T2）增量更新。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ToleranceThreshold(Base):
    """用户对某食物的个性化耐受阈值（贝叶斯后验落库）。"""

    __tablename__ = "tolerance_thresholds"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="关联用户"
    )
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), index=True, comment="关联食物"
    )
    # log 空间先验（来自 A6 知识库）
    prior_mean: Mapped[float] = mapped_column(Float, default=0.0, comment="先验均值（log 空间）")
    prior_var: Mapped[float] = mapped_column(Float, default=1.0, comment="先验方差（log 空间）")
    # 上次后验
    post_mean: Mapped[float] = mapped_column(Float, default=0.0, comment="后验均值（log 空间）")
    post_var: Mapped[float] = mapped_column(Float, default=1.0, comment="后验方差（log 空间）")
    # 三色分位剂量（克）
    safe_g: Mapped[int] = mapped_column(Integer, default=0, comment="安全剂量（5% 分位）")
    caution_g: Mapped[int] = mapped_column(Integer, default=0, comment="谨慎剂量（中位数）")
    unsafe_g: Mapped[int] = mapped_column(Integer, default=0, comment="不安全剂量（95% 分位）")
    n_obs: Mapped[int] = mapped_column(Integer, default=0, comment="观测数")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    user: Mapped["User"] = relationship(back_populates="tolerance_thresholds")
    food: Mapped["Food"] = relationship(back_populates="tolerance_thresholds")


from app.models.user import User  # noqa: E402
from app.models.food import Food  # noqa: E402
