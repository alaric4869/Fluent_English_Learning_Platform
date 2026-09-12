"""Create the initial IELTS practice schema.

Revision ID: 0001_ielts_baseline
Revises:
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_ielts_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ielts_practice_sets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("book_number", sa.Integer(), nullable=False),
        sa.Column("test_number", sa.Integer(), nullable=False),
        sa.Column("skill", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("content_version", sa.String(length=40), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ielts_practice_sets_skill", "ielts_practice_sets", ["skill"])
    op.create_index("ix_ielts_practice_sets_slug", "ielts_practice_sets", ["slug"], unique=True)

    op.create_table(
        "ielts_practice_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("practice_set_id", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("content_blocks", sa.JSON(), nullable=False),
        sa.Column("audio_path", sa.String(length=300), nullable=True),
        sa.ForeignKeyConstraint(["practice_set_id"], ["ielts_practice_sets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("practice_set_id", "order_index"),
    )
    op.create_index(
        "ix_ielts_practice_sections_practice_set_id",
        "ielts_practice_sections",
        ["practice_set_id"],
    )

    op.create_table(
        "ielts_practice_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("practice_set_id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=40), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("accepted_answers", sa.JSON(), nullable=False),
        sa.Column("answer_group", sa.String(length=80), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["practice_set_id"], ["ielts_practice_sets.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["ielts_practice_sections.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("practice_set_id", "number"),
    )
    op.create_index(
        "ix_ielts_practice_questions_practice_set_id",
        "ielts_practice_questions",
        ["practice_set_id"],
    )
    op.create_index(
        "ix_ielts_practice_questions_section_id",
        "ielts_practice_questions",
        ["section_id"],
    )

    op.create_table(
        "ielts_practice_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("practice_set_id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["practice_set_id"], ["ielts_practice_sets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("practice_set_id", "user_key"),
    )
    op.create_index(
        "ix_ielts_practice_attempts_practice_set_id",
        "ielts_practice_attempts",
        ["practice_set_id"],
    )
    op.create_index("ix_ielts_practice_attempts_user_key", "ielts_practice_attempts", ["user_key"])


def downgrade() -> None:
    op.drop_index("ix_ielts_practice_attempts_user_key", table_name="ielts_practice_attempts")
    op.drop_index(
        "ix_ielts_practice_attempts_practice_set_id",
        table_name="ielts_practice_attempts",
    )
    op.drop_table("ielts_practice_attempts")
    op.drop_index(
        "ix_ielts_practice_questions_section_id",
        table_name="ielts_practice_questions",
    )
    op.drop_index(
        "ix_ielts_practice_questions_practice_set_id",
        table_name="ielts_practice_questions",
    )
    op.drop_table("ielts_practice_questions")
    op.drop_index(
        "ix_ielts_practice_sections_practice_set_id",
        table_name="ielts_practice_sections",
    )
    op.drop_table("ielts_practice_sections")
    op.drop_index("ix_ielts_practice_sets_slug", table_name="ielts_practice_sets")
    op.drop_index("ix_ielts_practice_sets_skill", table_name="ielts_practice_sets")
    op.drop_table("ielts_practice_sets")
