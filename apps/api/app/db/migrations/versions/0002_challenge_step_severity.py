"""T2：为 challenge_steps 增加 severity 列（反应严重度 0~10）。

Revision ID: 0002_challenge_step_severity
Revises: 0001_initial
Create Date: 2025-07-24

说明：
- ``severity`` 记录每次微挑战步骤的反应严重度（0 = 无症状），由挑战步骤回写后驱
  贝叶斯后验更新（见 ``services/tolerance``）。
- 与 ``0001_initial`` 同样使用 ``app.db.base.JSONB``，PostgreSQL / SQLite 双方言兼容。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_challenge_step_severity"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "challenge_steps",
        sa.Column("severity", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("challenge_steps", "severity")
