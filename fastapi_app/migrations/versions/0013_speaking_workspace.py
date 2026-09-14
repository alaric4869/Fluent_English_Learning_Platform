"""Add persistent speaking workspace progress and submissions.

Revision ID: 0013_speaking_workspace
Revises: 0012_writing_practice
Create Date: 2026-09-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0013_speaking_workspace"
down_revision: str | None = "0012_writing_practice"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("speaking_retelling_records", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column("retelling_text", sa.Text(), nullable=False, server_default="")
        )
        batch_op.add_column(
            sa.Column(
                "workspace_managed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "active_duration_seconds",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(sa.Column("perceived_difficulty", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("confidence", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=30),
                nullable=False,
                server_default="in_progress",
            )
        )
        batch_op.add_column(
            sa.Column(
                "submission_revision",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_index(
            "ix_speaking_retelling_records_workspace_managed",
            ["workspace_managed"],
            unique=False,
        )
        batch_op.create_index(
            "ix_speaking_retelling_records_status", ["status"], unique=False
        )

    op.execute(
        sa.text(
            "UPDATE speaking_retelling_records "
            "SET started_at = created_at WHERE started_at IS NULL"
        )
    )
    with op.batch_alter_table("speaking_retelling_records", recreate="always") as batch_op:
        batch_op.alter_column(
            "started_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
        )

    op.create_table(
        "speaking_sentence_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("sentence_key", sa.String(length=120), nullable=False),
        sa.Column("practice_status", sa.String(length=40), nullable=False),
        sa.Column("practice_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["resource_id"], ["learning_resources.id"]),
        sa.UniqueConstraint("user_key", "resource_id", "sentence_key"),
    )
    op.create_index(
        "ix_speaking_sentence_progress_user_key",
        "speaking_sentence_progress",
        ["user_key"],
    )
    op.create_index(
        "ix_speaking_sentence_progress_resource_id",
        "speaking_sentence_progress",
        ["resource_id"],
    )
    op.create_index(
        "ix_speaking_sentence_progress_practice_status",
        "speaking_sentence_progress",
        ["practice_status"],
    )

    op.create_table(
        "speaking_retelling_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("retelling_record_id", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column(
            "written_outline_snapshot", sa.Text(), nullable=False, server_default=""
        ),
        sa.Column(
            "intended_vocabulary_snapshot", sa.JSON(), nullable=False
        ),
        sa.Column(
            "retelling_text_snapshot", sa.Text(), nullable=False, server_default=""
        ),
        sa.Column("mistakes_snapshot", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "improved_version_snapshot", sa.Text(), nullable=False, server_default=""
        ),
        sa.Column("practice_status", sa.String(length=40), nullable=False),
        sa.Column(
            "active_duration_seconds",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("perceived_difficulty", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["retelling_record_id"], ["speaking_retelling_records.id"]
        ),
        sa.UniqueConstraint("retelling_record_id", "revision"),
    )
    op.create_index(
        "ix_speaking_retelling_submissions_retelling_record_id",
        "speaking_retelling_submissions",
        ["retelling_record_id"],
    )
    op.create_index(
        "ix_speaking_retelling_submissions_submitted_at",
        "speaking_retelling_submissions",
        ["submitted_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_speaking_retelling_submissions_submitted_at",
        table_name="speaking_retelling_submissions",
    )
    op.drop_index(
        "ix_speaking_retelling_submissions_retelling_record_id",
        table_name="speaking_retelling_submissions",
    )
    op.drop_table("speaking_retelling_submissions")
    op.drop_index(
        "ix_speaking_sentence_progress_practice_status",
        table_name="speaking_sentence_progress",
    )
    op.drop_index(
        "ix_speaking_sentence_progress_resource_id",
        table_name="speaking_sentence_progress",
    )
    op.drop_index(
        "ix_speaking_sentence_progress_user_key",
        table_name="speaking_sentence_progress",
    )
    op.drop_table("speaking_sentence_progress")

    with op.batch_alter_table("speaking_retelling_records", recreate="always") as batch_op:
        batch_op.drop_index("ix_speaking_retelling_records_status")
        batch_op.drop_index("ix_speaking_retelling_records_workspace_managed")
        batch_op.drop_column("submitted_at")
        batch_op.drop_column("started_at")
        batch_op.drop_column("submission_revision")
        batch_op.drop_column("status")
        batch_op.drop_column("confidence")
        batch_op.drop_column("perceived_difficulty")
        batch_op.drop_column("active_duration_seconds")
        batch_op.drop_column("workspace_managed")
        batch_op.drop_column("retelling_text")
