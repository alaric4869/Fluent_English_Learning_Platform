"""Link learner responses to saved AI plan recommendations.

Revision ID: 0016_ai_recommendation_responses
Revises: 0015_weekly_coaching_reports
Create Date: 2026-09-22
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0016_ai_recommendation_responses"
down_revision: str | None = "0015_weekly_coaching_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("adaptation_decisions") as batch_op:
        batch_op.add_column(
            sa.Column("source_decision_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_adaptation_decisions_source_decision_id",
            "adaptation_decisions",
            ["source_decision_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_adaptation_decisions_source_decision_id",
            ["source_decision_id"],
            unique=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("adaptation_decisions") as batch_op:
        batch_op.drop_index("ix_adaptation_decisions_source_decision_id")
        batch_op.drop_constraint(
            "fk_adaptation_decisions_source_decision_id",
            type_="foreignkey",
        )
        batch_op.drop_column("source_decision_id")
