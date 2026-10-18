"""Add generic learning resources and the learning evidence pipeline.

Revision ID: 0002_learning_evidence
Revises: 0001_ielts_baseline
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_learning_evidence"
down_revision: str | None = "0001_ielts_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learning_resources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("resource_type", sa.String(length=60), nullable=False),
        sa.Column("skill", sa.String(length=30), nullable=False),
        sa.Column("topic", sa.String(length=120), nullable=False),
        sa.Column("difficulty", sa.String(length=40), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("local_asset_reference", sa.String(length=500), nullable=True),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_learning_resources_resource_type", "learning_resources", ["resource_type"])
    op.create_index("ix_learning_resources_skill", "learning_resources", ["skill"])
    op.create_index("ix_learning_resources_slug", "learning_resources", ["slug"], unique=True)

    with op.batch_alter_table("ielts_practice_sets") as batch_op:
        batch_op.add_column(sa.Column("learning_resource_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_ielts_practice_sets_learning_resource_id",
            "learning_resources",
            ["learning_resource_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_ielts_practice_sets_learning_resource_id",
            ["learning_resource_id"],
        )

    with op.batch_alter_table("ielts_practice_attempts") as batch_op:
        batch_op.add_column(
            sa.Column("submission_revision", sa.Integer(), server_default="0", nullable=False)
        )

    op.create_table(
        "study_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("skill", sa.String(length=30), nullable=False),
        sa.Column("source_type", sa.String(length=60), nullable=False),
        sa.Column("source_id", sa.String(length=120), nullable=False),
        sa.Column("source_revision", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("perceived_difficulty", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("hard_item_count", sa.Integer(), nullable=True),
        sa.Column("incorrect_item_count", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["resource_id"], ["learning_resources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_key", "source_type", "source_id", "source_revision"),
    )
    op.create_index("ix_study_sessions_completed_at", "study_sessions", ["completed_at"])
    op.create_index("ix_study_sessions_resource_id", "study_sessions", ["resource_id"])
    op.create_index("ix_study_sessions_skill", "study_sessions", ["skill"])
    op.create_index("ix_study_sessions_user_key", "study_sessions", ["user_key"])

    op.create_table(
        "exercise_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("study_session_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.String(length=180), nullable=False),
        sa.Column("submitted_answer", sa.Text(), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("prompt_snapshot", sa.Text(), nullable=False),
        sa.Column("correct_answers", sa.JSON(), nullable=False),
        sa.Column("explanation_snapshot", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["study_session_id"], ["study_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("study_session_id", "exercise_id"),
    )
    op.create_index("ix_exercise_attempts_study_session_id", "exercise_attempts", ["study_session_id"])

    op.create_table(
        "skill_performances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("study_session_id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("skill", sa.String(length=30), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("correct_item_count", sa.Integer(), nullable=False),
        sa.Column("incorrect_item_count", sa.Integer(), nullable=False),
        sa.Column("hard_item_count", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("perceived_difficulty", sa.Integer(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["study_session_id"], ["study_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("study_session_id", "skill"),
    )
    op.create_index("ix_skill_performances_occurred_at", "skill_performances", ["occurred_at"])
    op.create_index("ix_skill_performances_skill", "skill_performances", ["skill"])
    op.create_index("ix_skill_performances_study_session_id", "skill_performances", ["study_session_id"])
    op.create_index("ix_skill_performances_user_key", "skill_performances", ["user_key"])


def downgrade() -> None:
    op.drop_index("ix_skill_performances_user_key", table_name="skill_performances")
    op.drop_index("ix_skill_performances_study_session_id", table_name="skill_performances")
    op.drop_index("ix_skill_performances_skill", table_name="skill_performances")
    op.drop_index("ix_skill_performances_occurred_at", table_name="skill_performances")
    op.drop_table("skill_performances")

    op.drop_index("ix_exercise_attempts_study_session_id", table_name="exercise_attempts")
    op.drop_table("exercise_attempts")

    op.drop_index("ix_study_sessions_user_key", table_name="study_sessions")
    op.drop_index("ix_study_sessions_skill", table_name="study_sessions")
    op.drop_index("ix_study_sessions_resource_id", table_name="study_sessions")
    op.drop_index("ix_study_sessions_completed_at", table_name="study_sessions")
    op.drop_table("study_sessions")

    with op.batch_alter_table("ielts_practice_attempts") as batch_op:
        batch_op.drop_column("submission_revision")

    with op.batch_alter_table("ielts_practice_sets") as batch_op:
        batch_op.drop_index("ix_ielts_practice_sets_learning_resource_id")
        batch_op.drop_constraint(
            "fk_ielts_practice_sets_learning_resource_id",
            type_="foreignkey",
        )
        batch_op.drop_column("learning_resource_id")

    op.drop_index("ix_learning_resources_slug", table_name="learning_resources")
    op.drop_index("ix_learning_resources_skill", table_name="learning_resources")
    op.drop_index("ix_learning_resources_resource_type", table_name="learning_resources")
    op.drop_table("learning_resources")
