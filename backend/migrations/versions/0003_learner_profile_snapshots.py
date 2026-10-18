"""Add learner profiles and immutable skill snapshots.

Revision ID: 0003_learner_profiles
Revises: 0002_learning_evidence
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_learner_profiles"
down_revision: str | None = "0002_learning_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learner_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_learner_profiles_user_key", "learner_profiles", ["user_key"], unique=True)

    op.create_table(
        "learner_profile_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("learner_profile_id", sa.Integer(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("algorithm_version", sa.String(length=60), nullable=False),
        sa.Column("evidence_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learner_profile_id"], ["learner_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("learner_profile_id", "algorithm_version", "evidence_fingerprint"),
    )
    op.create_index(
        "ix_learner_profile_snapshots_calculated_at",
        "learner_profile_snapshots",
        ["calculated_at"],
    )
    op.create_index(
        "ix_learner_profile_snapshots_learner_profile_id",
        "learner_profile_snapshots",
        ["learner_profile_id"],
    )

    op.create_table(
        "learner_skill_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_snapshot_id", sa.Integer(), nullable=False),
        sa.Column("skill", sa.String(length=30), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("evidence_status", sa.String(length=30), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("average_accuracy", sa.Float(), nullable=True),
        sa.Column("average_confidence", sa.Float(), nullable=True),
        sa.Column("average_difficulty", sa.Float(), nullable=True),
        sa.Column("hard_item_rate", sa.Float(), nullable=True),
        sa.Column("accuracy_trend", sa.Float(), nullable=True),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("calculation_weights", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_snapshot_id"], ["learner_profile_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_snapshot_id", "skill"),
    )
    op.create_index("ix_learner_skill_snapshots_skill", "learner_skill_snapshots", ["skill"])
    op.create_index(
        "ix_learner_skill_snapshots_profile_snapshot_id",
        "learner_skill_snapshots",
        ["profile_snapshot_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_learner_skill_snapshots_profile_snapshot_id",
        table_name="learner_skill_snapshots",
    )
    op.drop_index("ix_learner_skill_snapshots_skill", table_name="learner_skill_snapshots")
    op.drop_table("learner_skill_snapshots")

    op.drop_index(
        "ix_learner_profile_snapshots_learner_profile_id",
        table_name="learner_profile_snapshots",
    )
    op.drop_index(
        "ix_learner_profile_snapshots_calculated_at",
        table_name="learner_profile_snapshots",
    )
    op.drop_table("learner_profile_snapshots")

    op.drop_index("ix_learner_profiles_user_key", table_name="learner_profiles")
    op.drop_table("learner_profiles")
