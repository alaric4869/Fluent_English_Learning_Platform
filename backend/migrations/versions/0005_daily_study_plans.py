"""Add resource priority and date-persisted study plans.

Revision ID: 0005_daily_study_plans
Revises: 0004_weakness_assessments
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0005_daily_study_plans"
down_revision: str | None = "0004_weakness_assessments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("learning_resources") as batch_op:
        batch_op.add_column(
            sa.Column("priority", sa.Integer(), server_default="50", nullable=False)
        )

    op.create_table(
        "study_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("generator_version", sa.String(length=60), nullable=False),
        sa.Column("weakness_assessment_run_id", sa.Integer(), nullable=True),
        sa.Column("recommender_version", sa.String(length=60), nullable=False),
        sa.Column("total_minutes", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["weakness_assessment_run_id"],
            ["weakness_assessment_runs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_key", "plan_date"),
    )
    op.create_index("ix_study_plans_plan_date", "study_plans", ["plan_date"])
    op.create_index("ix_study_plans_status", "study_plans", ["status"])
    op.create_index("ix_study_plans_user_key", "study_plans", ["user_key"])
    op.create_index(
        "ix_study_plans_weakness_assessment_run_id",
        "study_plans",
        ["weakness_assessment_run_id"],
    )

    op.create_table(
        "study_plan_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("study_plan_id", sa.Integer(), nullable=False),
        sa.Column("skill", sa.String(length=30), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("system_planned_minutes", sa.Integer(), nullable=False),
        sa.Column("planned_minutes", sa.Integer(), nullable=False),
        sa.Column("system_resource_id", sa.Integer(), nullable=True),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("recommendation_score", sa.Float(), nullable=True),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("manual_override", sa.Boolean(), nullable=False),
        sa.Column("override_note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["resource_id"], ["learning_resources.id"]),
        sa.ForeignKeyConstraint(["study_plan_id"], ["study_plans.id"]),
        sa.ForeignKeyConstraint(["system_resource_id"], ["learning_resources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("study_plan_id", "position"),
        sa.UniqueConstraint("study_plan_id", "skill"),
    )
    op.create_index("ix_study_plan_items_skill", "study_plan_items", ["skill"])
    op.create_index("ix_study_plan_items_status", "study_plan_items", ["status"])
    op.create_index(
        "ix_study_plan_items_study_plan_id",
        "study_plan_items",
        ["study_plan_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_study_plan_items_study_plan_id", table_name="study_plan_items")
    op.drop_index("ix_study_plan_items_status", table_name="study_plan_items")
    op.drop_index("ix_study_plan_items_skill", table_name="study_plan_items")
    op.drop_table("study_plan_items")

    op.drop_index(
        "ix_study_plans_weakness_assessment_run_id",
        table_name="study_plans",
    )
    op.drop_index("ix_study_plans_user_key", table_name="study_plans")
    op.drop_index("ix_study_plans_status", table_name="study_plans")
    op.drop_index("ix_study_plans_plan_date", table_name="study_plans")
    op.drop_table("study_plans")

    with op.batch_alter_table("learning_resources") as batch_op:
        batch_op.drop_column("priority")
