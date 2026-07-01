"""add user feedback

Revision ID: 20260701_0004
Revises: 20260701_0003
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260701_0004"
down_revision = "20260701_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_feedback",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("feature", sa.String(length=100), nullable=False),
        sa.Column("feedback_type", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_feedback_user_status", "user_feedback", ["user_id", "status"], unique=False)
    op.create_index(op.f("ix_user_feedback_user_id"), "user_feedback", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_feedback_user_id"), table_name="user_feedback")
    op.drop_index("ix_user_feedback_user_status", table_name="user_feedback")
    op.drop_table("user_feedback")
