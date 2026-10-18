"""Persist explicit AI weekly coaching reports.

Revision ID: 0015_weekly_coaching_reports
Revises: 0014_work_evaluations
Create Date: 2026-09-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0015_weekly_coaching_reports"
down_revision: str | None = "0014_work_evaluations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weekly_coaching_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("provider_name", sa.String(length=60), nullable=False),
        sa.Column("response_id", sa.String(length=200), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=False),
        sa.Column("tools_used", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("user_key", "week_start", "provider_name", "created_at"):
        op.create_index(
            f"ix_weekly_coaching_reports_{column}",
            "weekly_coaching_reports",
            [column],
        )


def downgrade() -> None:
    for column in reversed(("user_key", "week_start", "provider_name", "created_at")):
        op.drop_index(
            f"ix_weekly_coaching_reports_{column}",
            table_name="weekly_coaching_reports",
        )
    op.drop_table("weekly_coaching_reports")
