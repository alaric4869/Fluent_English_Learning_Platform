"""Add explainable weakness assessment history.

Revision ID: 0004_weakness_assessments
Revises: 0003_learner_profiles
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004_weakness_assessments"
down_revision: str | None = "0003_learner_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weakness_assessment_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("learner_profile_id", sa.Integer(), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detector_version", sa.String(length=60), nullable=False),
        sa.Column("evidence_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learner_profile_id"], ["learner_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("learner_profile_id", "detector_version", "evidence_fingerprint"),
    )
    op.create_index(
        "ix_weakness_assessment_runs_assessed_at",
        "weakness_assessment_runs",
        ["assessed_at"],
    )
    op.create_index(
        "ix_weakness_assessment_runs_learner_profile_id",
        "weakness_assessment_runs",
        ["learner_profile_id"],
    )

    op.create_table(
        "weakness_skill_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_run_id", sa.Integer(), nullable=False),
        sa.Column("skill", sa.String(length=30), nullable=False),
        sa.Column("classification", sa.String(length=40), nullable=False),
        sa.Column("smoothed_score", sa.Float(), nullable=True),
        sa.Column("latest_score", sa.Float(), nullable=True),
        sa.Column("scored_snapshot_count", sa.Integer(), nullable=False),
        sa.Column("latest_average_accuracy", sa.Float(), nullable=True),
        sa.Column("latest_average_confidence", sa.Float(), nullable=True),
        sa.Column("latest_hard_item_rate", sa.Float(), nullable=True),
        sa.Column("latest_accuracy_trend", sa.Float(), nullable=True),
        sa.Column("evidence_snapshot_ids", sa.JSON(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_run_id"], ["weakness_assessment_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_run_id", "skill"),
    )
    op.create_index(
        "ix_weakness_skill_assessments_assessment_run_id",
        "weakness_skill_assessments",
        ["assessment_run_id"],
    )
    op.create_index(
        "ix_weakness_skill_assessments_classification",
        "weakness_skill_assessments",
        ["classification"],
    )
    op.create_index(
        "ix_weakness_skill_assessments_skill",
        "weakness_skill_assessments",
        ["skill"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_weakness_skill_assessments_skill",
        table_name="weakness_skill_assessments",
    )
    op.drop_index(
        "ix_weakness_skill_assessments_classification",
        table_name="weakness_skill_assessments",
    )
    op.drop_index(
        "ix_weakness_skill_assessments_assessment_run_id",
        table_name="weakness_skill_assessments",
    )
    op.drop_table("weakness_skill_assessments")

    op.drop_index(
        "ix_weakness_assessment_runs_learner_profile_id",
        table_name="weakness_assessment_runs",
    )
    op.drop_index(
        "ix_weakness_assessment_runs_assessed_at",
        table_name="weakness_assessment_runs",
    )
    op.drop_table("weakness_assessment_runs")
