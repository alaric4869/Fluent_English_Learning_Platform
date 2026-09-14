"""Add persistent IELTS writing drafts and submissions.

Revision ID: 0012_writing_practice
Revises: 0011_module_sessions
Create Date: 2026-09-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0012_writing_practice"
down_revision: str | None = "0011_module_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "writing_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("outline", sa.Text(), nullable=False, server_default=""),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "active_duration_seconds", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("perceived_difficulty", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column(
            "status", sa.String(length=30), nullable=False, server_default="in_progress"
        ),
        sa.Column("submission_revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["resource_id"], ["learning_resources.id"]),
        sa.UniqueConstraint("user_key", "resource_id"),
    )
    op.create_index("ix_writing_drafts_user_key", "writing_drafts", ["user_key"])
    op.create_index("ix_writing_drafts_resource_id", "writing_drafts", ["resource_id"])
    op.create_index("ix_writing_drafts_status", "writing_drafts", ["status"])

    op.create_table(
        "writing_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("writing_draft_id", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("response_snapshot", sa.Text(), nullable=False),
        sa.Column("outline_snapshot", sa.Text(), nullable=False, server_default=""),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column(
            "active_duration_seconds", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("perceived_difficulty", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["writing_draft_id"], ["writing_drafts.id"]),
        sa.UniqueConstraint("writing_draft_id", "revision"),
    )
    op.create_index(
        "ix_writing_submissions_writing_draft_id",
        "writing_submissions",
        ["writing_draft_id"],
    )
    op.create_index(
        "ix_writing_submissions_submitted_at",
        "writing_submissions",
        ["submitted_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_writing_submissions_submitted_at", table_name="writing_submissions"
    )
    op.drop_index(
        "ix_writing_submissions_writing_draft_id", table_name="writing_submissions"
    )
    op.drop_table("writing_submissions")
    op.drop_index("ix_writing_drafts_status", table_name="writing_drafts")
    op.drop_index("ix_writing_drafts_resource_id", table_name="writing_drafts")
    op.drop_index("ix_writing_drafts_user_key", table_name="writing_drafts")
    op.drop_table("writing_drafts")
