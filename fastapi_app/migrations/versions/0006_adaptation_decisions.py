"""Add explainable adaptation decision history.

Revision ID: 0006_adaptation_decisions
Revises: 0005_daily_study_plans
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006_adaptation_decisions"
down_revision: str | None = "0005_daily_study_plans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "adaptation_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("study_plan_id", sa.Integer(), nullable=False),
        sa.Column("study_plan_item_id", sa.Integer(), nullable=False),
        sa.Column("decision_type", sa.String(length=40), nullable=False),
        sa.Column("actor", sa.String(length=30), nullable=False),
        sa.Column("skill", sa.String(length=30), nullable=False),
        sa.Column("previous_planned_minutes", sa.Integer(), nullable=False),
        sa.Column("new_planned_minutes", sa.Integer(), nullable=False),
        sa.Column("previous_resource_id", sa.Integer(), nullable=True),
        sa.Column("new_resource_id", sa.Integer(), nullable=True),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["new_resource_id"], ["learning_resources.id"]),
        sa.ForeignKeyConstraint(["previous_resource_id"], ["learning_resources.id"]),
        sa.ForeignKeyConstraint(["study_plan_id"], ["study_plans.id"]),
        sa.ForeignKeyConstraint(["study_plan_item_id"], ["study_plan_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_adaptation_decisions_actor",
        "adaptation_decisions",
        ["actor"],
    )
    op.create_index(
        "ix_adaptation_decisions_decision_type",
        "adaptation_decisions",
        ["decision_type"],
    )
    op.create_index(
        "ix_adaptation_decisions_skill",
        "adaptation_decisions",
        ["skill"],
    )
    op.create_index(
        "ix_adaptation_decisions_study_plan_id",
        "adaptation_decisions",
        ["study_plan_id"],
    )
    op.create_index(
        "ix_adaptation_decisions_study_plan_item_id",
        "adaptation_decisions",
        ["study_plan_item_id"],
    )
    op.execute(
        sa.text(
            """
            INSERT INTO adaptation_decisions (
                study_plan_id,
                study_plan_item_id,
                decision_type,
                actor,
                skill,
                previous_planned_minutes,
                new_planned_minutes,
                previous_resource_id,
                new_resource_id,
                reasons,
                created_at
            )
            SELECT
                item.study_plan_id,
                item.id,
                'system_recommendation',
                'rule_based',
                item.skill,
                CASE item.skill
                    WHEN 'listening' THEN 30
                    WHEN 'speaking' THEN 25
                    WHEN 'reading' THEN 30
                    WHEN 'vocabulary' THEN 25
                    ELSE item.system_planned_minutes
                END,
                item.system_planned_minutes,
                NULL,
                item.system_resource_id,
                item.reasons,
                item.created_at
            FROM study_plan_items AS item
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_adaptation_decisions_study_plan_item_id",
        table_name="adaptation_decisions",
    )
    op.drop_index(
        "ix_adaptation_decisions_study_plan_id",
        table_name="adaptation_decisions",
    )
    op.drop_index("ix_adaptation_decisions_skill", table_name="adaptation_decisions")
    op.drop_index(
        "ix_adaptation_decisions_decision_type",
        table_name="adaptation_decisions",
    )
    op.drop_index("ix_adaptation_decisions_actor", table_name="adaptation_decisions")
    op.drop_table("adaptation_decisions")
