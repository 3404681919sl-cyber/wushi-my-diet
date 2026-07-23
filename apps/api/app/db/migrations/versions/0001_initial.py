"""初始建表：用户 / 画像 / 状况 / 症状 / 餐 / 挑战 / 食物 / 耐受阈值

Revision ID: 0001_initial
Revises:
Create Date: 2025-07-23

说明：
- 使用 ``app.db.base.JSONB``：PostgreSQL 下编译为 JSONB，SQLite 下自动编译为 JSON，
  保证单一迁移脚本在两种数据库均可执行（开发 / 测试用 SQLite，生产用 PostgreSQL）。
- 所有用户级子表均带 ``ondelete="CASCADE"``，删除用户时级联清理。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.base import JSONB

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- users ----------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("nickname", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("wechat_union_id", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("wechat_union_id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_wechat_union_id", "users", ["wechat_union_id"], unique=True)

    # ---------- profiles (1:1 users) ----------
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_weights", JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"], unique=True)

    # ---------- conditions (1:* users) ----------
    op.create_table(
        "conditions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("fodmap_flags", JSONB(), nullable=False),
        sa.Column("glucose_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("histamine_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("note", sa.String(length=512), nullable=False, server_default=""),
    )
    op.create_index("ix_conditions_user_id", "conditions", ["user_id"])

    # ---------- symptom_defs (1:* users) ----------
    op.create_table(
        "symptom_defs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("scale_max", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("is_custom", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_symptom_defs_user_id", "symptom_defs", ["user_id"])

    # ---------- symptom_logs (1:* users, *:1 symptom_defs) ----------
    op.create_table(
        "symptom_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "symptom_def_id",
            sa.Integer(),
            sa.ForeignKey("symptom_defs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("severity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "logged_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_symptom_logs_user_id", "symptom_logs", ["user_id"])
    op.create_index("ix_symptom_logs_symptom_def_id", "symptom_logs", ["symptom_def_id"])

    # ---------- foods ----------
    op.create_table(
        "foods",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("fodmap_category", JSONB(), nullable=False),
        sa.Column("gi", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("gl_per_100g", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("histamine_level", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("nutrients", JSONB(), nullable=False),
        sa.Column("is_preset", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_foods_name", "foods", ["name"], unique=True)

    # ---------- meal_logs (1:* users) ----------
    op.create_table(
        "meal_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "logged_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("note", sa.String(length=512), nullable=False, server_default=""),
    )
    op.create_index("ix_meal_logs_user_id", "meal_logs", ["user_id"])

    # ---------- meal_items (1:* meal_logs, *:1 foods) ----------
    op.create_table(
        "meal_items",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "meal_log_id",
            sa.Integer(),
            sa.ForeignKey("meal_logs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "food_id",
            sa.Integer(),
            sa.ForeignKey("foods.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount_g", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.create_index("ix_meal_items_meal_log_id", "meal_items", ["meal_log_id"])
    op.create_index("ix_meal_items_food_id", "meal_items", ["food_id"])

    # ---------- challenges (1:* users, *:1 foods) ----------
    op.create_table(
        "challenges",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "food_id",
            sa.Integer(),
            sa.ForeignKey("foods.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_challenges_user_id", "challenges", ["user_id"])
    op.create_index("ix_challenges_food_id", "challenges", ["food_id"])

    # ---------- challenge_steps (1:* challenges) ----------
    op.create_table(
        "challenge_steps",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "challenge_id",
            sa.Integer(),
            sa.ForeignKey("challenges.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("dose_g", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result", sa.String(length=32), nullable=True),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_challenge_steps_challenge_id", "challenge_steps", ["challenge_id"])

    # ---------- tolerance_thresholds (1:* users, *:1 foods) ----------
    op.create_table(
        "tolerance_thresholds",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "food_id",
            sa.Integer(),
            sa.ForeignKey("foods.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prior_mean", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("prior_var", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("post_mean", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("post_var", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("safe_g", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("caution_g", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unsafe_g", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("n_obs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_tolerance_thresholds_user_id", "tolerance_thresholds", ["user_id"])
    op.create_index("ix_tolerance_thresholds_food_id", "tolerance_thresholds", ["food_id"])


def downgrade() -> None:
    op.drop_table("tolerance_thresholds")
    op.drop_table("challenge_steps")
    op.drop_table("challenges")
    op.drop_table("meal_items")
    op.drop_table("meal_logs")
    op.drop_table("foods")
    op.drop_table("symptom_logs")
    op.drop_table("symptom_defs")
    op.drop_table("conditions")
    op.drop_table("profiles")
    op.drop_table("users")
