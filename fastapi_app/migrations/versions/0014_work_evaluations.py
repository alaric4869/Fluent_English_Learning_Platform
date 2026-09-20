"""Add provider-neutral evaluations for learner-authored work.

Revision ID: 0014_work_evaluations
Revises: 0013_speaking_workspace
Create Date: 2026-09-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0014_work_evaluations"
down_revision: str | None = "0013_speaking_workspace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "work_evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("skill", sa.String(length=30), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("source_revision", sa.Integer(), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("task_prompt", sa.Text(), nullable=False),
        sa.Column("learner_text", sa.Text(), nullable=False),
        sa.Column("supporting_context", sa.Text(), nullable=False),
        sa.Column("provider_name", sa.String(length=60), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("evaluator_version", sa.String(length=120), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("improvement_priorities", sa.JSON(), nullable=False),
        sa.Column("corrections", sa.JSON(), nullable=False),
        sa.Column("suggested_revision", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["resource_id"], ["learning_resources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_key",
            "source_type",
            "source_id",
            "source_revision",
            "evaluator_version",
            "input_fingerprint",
            name="uq_work_evaluation_identity",
        ),
    )
    for column in (
        "user_key",
        "resource_id",
        "skill",
        "source_type",
        "source_id",
        "provider_name",
        "evaluator_version",
    ):
        op.create_index(
            f"ix_work_evaluations_{column}",
            "work_evaluations",
            [column],
        )


def downgrade() -> None:
    for column in reversed(
        (
            "user_key",
            "resource_id",
            "skill",
            "source_type",
            "source_id",
            "provider_name",
            "evaluator_version",
        )
    ):
        op.drop_index(
            f"ix_work_evaluations_{column}",
            table_name="work_evaluations",
        )
    op.drop_table("work_evaluations")
