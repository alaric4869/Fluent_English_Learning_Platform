"""Allow timed non-question study sessions.

Revision ID: 0011_module_sessions
Revises: 0010_resource_library
Create Date: 2026-09-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0011_module_sessions"
down_revision: str | None = "0010_resource_library"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("study_sessions") as batch_op:
        batch_op.alter_column(
            "completed_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
        )
        batch_op.alter_column(
            "accuracy",
            existing_type=sa.Float(),
            nullable=True,
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.current_timestamp(),
                nullable=False,
            )
        )

    with op.batch_alter_table("skill_performances") as batch_op:
        batch_op.alter_column(
            "accuracy",
            existing_type=sa.Float(),
            nullable=True,
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM skill_performances WHERE study_session_id IN "
            "(SELECT id FROM study_sessions WHERE source_type = 'study_plan_item')"
        )
    )
    connection.execute(
        sa.text("DELETE FROM study_sessions WHERE source_type = 'study_plan_item'")
    )

    with op.batch_alter_table("skill_performances") as batch_op:
        batch_op.alter_column(
            "accuracy",
            existing_type=sa.Float(),
            nullable=False,
        )

    with op.batch_alter_table("study_sessions") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.alter_column(
            "accuracy",
            existing_type=sa.Float(),
            nullable=False,
        )
        batch_op.alter_column(
            "completed_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
        )
