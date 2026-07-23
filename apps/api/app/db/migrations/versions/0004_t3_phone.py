"""T3 用户手机号登录：users 表追加 phone 列（唯一、索引、可空兼容旧数据）。

Revision ID: 0004_t3_phone
Revises: 0003_t2_columns
Create Date: 2025-07-23

说明：
- 产品决策改为「手机号 + 密码」登录，不再以邮箱为主标识。
- phone 设为唯一索引；可空以兼容存量数据（旧账号无手机号）；
  模型层 ``User.phone`` 为非空，应用层保证新注册必填手机号。
- 邮箱列保留为可空可选字段，不删除，避免破坏既有数据与外键引用。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_t3_phone"
down_revision: Union[str, None] = "0003_t2_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users.phone：手机号作为登录标识（唯一、索引）
    op.add_column(
        "users",
        sa.Column("phone", sa.String(20), nullable=True, index=True, unique=True),
    )


def downgrade() -> None:
    op.drop_column("users", "phone")
