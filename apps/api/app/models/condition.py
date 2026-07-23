"""健康状况（多状况录入）模型。

每位用户可录入多个诊断 / 状况（IBS、糖尿病、SIBO、组胺不耐等）。每条可标注冲突维度：
``fodmap_flags``（JSONB，六类 FODMAP 的触发标记）、``glucose_flag``（升糖）、
``histamine_flag``（组胺）。``is_active`` 支持用户覆盖（B6）。
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONB


class Condition(Base):
    """用户录入的健康状况。"""

    __tablename__ = "conditions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="关联用户"
    )
    name: Mapped[str] = mapped_column(String(128), comment="状况名称（如 IBS-D）")
    # FODMAP 六类触发标记，如 {"fructan": true, "lactose": true}
    fodmap_flags: Mapped[dict] = mapped_column(
        JSONB, default=dict, comment="FODMAP 各维度触发标记（JSONB）"
    )
    glucose_flag: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否涉及升糖维度")
    histamine_flag: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否涉及组胺维度")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否启用（用户可覆盖，B6）"
    )
    note: Mapped[str] = mapped_column(String(512), default="", comment="备注")

    user: Mapped["User"] = relationship(back_populates="conditions")


from app.models.user import User  # noqa: E402
