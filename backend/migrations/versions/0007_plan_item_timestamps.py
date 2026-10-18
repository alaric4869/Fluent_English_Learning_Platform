"""Add study plan item activity timestamps.

Revision ID: 0007_plan_item_timestamps
Revises: 0006_adaptation_decisions
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007_plan_item_timestamps"
down_revision: str | None = "0006_adaptation_decisions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("study_plan_items") as batch_op:
        batch_op.add_column(
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_index(
            "ix_study_plan_items_completed_at",
            ["completed_at"],
        )


def downgrade() -> None:
    with op.batch_alter_table("study_plan_items") as batch_op:
        batch_op.drop_index("ix_study_plan_items_completed_at")
        batch_op.drop_column("completed_at")
        batch_op.drop_column("started_at")
