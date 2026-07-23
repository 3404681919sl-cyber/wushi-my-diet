"""T2 追加列：conditions.override_json（覆盖规则，B6 预留）。

Revision ID: 0003_t2_columns
Revises: 0002_challenge_step_severity
Create Date: 2025-07-23

说明：
- ``challenge_steps.severity`` 已由 ``0002_challenge_step_severity`` 追加，本迁移仅负责
  ``conditions.override_json``（覆盖规则，如豁免某食物冲突），避免重复添加同一列。
- 可空 / 带默认值的追加列，向前兼容 T1 已建表。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.base import JSONB

# revision identifiers, used by Alembic.
revision: str = "0003_t2_columns"
down_revision: Union[str, None] = "0002_challenge_step_severity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # conditions.override_json
    op.add_column(
        "conditions",
        sa.Column("override_json", JSONB(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("conditions", "override_json")
