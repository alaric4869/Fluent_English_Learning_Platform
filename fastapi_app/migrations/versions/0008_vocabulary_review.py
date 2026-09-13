"""Add vocabulary chunks and spaced review history.

Revision ID: 0008_vocabulary_review
Revises: 0007_plan_item_timestamps
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008_vocabulary_review"
down_revision: str | None = "0007_plan_item_timestamps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vocabulary_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("chunk", sa.String(length=300), nullable=False),
        sa.Column("normalized_chunk", sa.String(length=300), nullable=False),
        sa.Column("meaning", sa.Text(), nullable=False),
        sa.Column("example_sentence", sa.Text(), nullable=False),
        sa.Column("learned_on", sa.Date(), nullable=False),
        sa.Column("personal_note", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=30), nullable=False),
        sa.Column("mastery_status", sa.String(length=30), nullable=False),
        sa.Column("source_resource_id", sa.Integer(), nullable=True),
        sa.Column("source_context", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("favorite", sa.Boolean(), nullable=False),
        sa.Column("saved_for_later", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_resource_id"], ["learning_resources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_key", "normalized_chunk"),
    )
    op.create_index("ix_vocabulary_items_difficulty", "vocabulary_items", ["difficulty"])
    op.create_index("ix_vocabulary_items_learned_on", "vocabulary_items", ["learned_on"])
    op.create_index(
        "ix_vocabulary_items_mastery_status",
        "vocabulary_items",
        ["mastery_status"],
    )
    op.create_index(
        "ix_vocabulary_items_source_resource_id",
        "vocabulary_items",
        ["source_resource_id"],
    )
    op.create_index("ix_vocabulary_items_user_key", "vocabulary_items", ["user_key"])

    op.create_table(
        "review_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("item_type", sa.String(length=40), nullable=False),
        sa.Column("vocabulary_item_id", sa.Integer(), nullable=False),
        sa.Column("scheduler_version", sa.String(length=60), nullable=False),
        sa.Column("schedule_step", sa.Integer(), nullable=False),
        sa.Column("next_review_date", sa.Date(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["vocabulary_item_id"], ["vocabulary_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vocabulary_item_id"),
    )
    op.create_index("ix_review_items_active", "review_items", ["active"])
    op.create_index("ix_review_items_item_type", "review_items", ["item_type"])
    op.create_index(
        "ix_review_items_next_review_date",
        "review_items",
        ["next_review_date"],
    )
    op.create_index(
        "ix_review_items_user_key_next_review_date",
        "review_items",
        ["user_key", "next_review_date"],
    )
    op.create_index("ix_review_items_user_key", "review_items", ["user_key"])

    op.create_table(
        "review_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("review_item_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("rating", sa.String(length=20), nullable=False),
        sa.Column("previous_step", sa.Integer(), nullable=False),
        sa.Column("next_step", sa.Integer(), nullable=False),
        sa.Column("previous_review_date", sa.Date(), nullable=False),
        sa.Column("next_review_date", sa.Date(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("previous_mastery_status", sa.String(length=30), nullable=False),
        sa.Column("new_mastery_status", sa.String(length=30), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["review_item_id"], ["review_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index("ix_review_attempts_rating", "review_attempts", ["rating"])
    op.create_index(
        "ix_review_attempts_request_id",
        "review_attempts",
        ["request_id"],
        unique=True,
    )
    op.create_index(
        "ix_review_attempts_review_item_id",
        "review_attempts",
        ["review_item_id"],
    )
    op.create_index(
        "ix_review_attempts_reviewed_at",
        "review_attempts",
        ["reviewed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_review_attempts_reviewed_at", table_name="review_attempts")
    op.drop_index("ix_review_attempts_review_item_id", table_name="review_attempts")
    op.drop_index("ix_review_attempts_request_id", table_name="review_attempts")
    op.drop_index("ix_review_attempts_rating", table_name="review_attempts")
    op.drop_table("review_attempts")

    op.drop_index("ix_review_items_user_key", table_name="review_items")
    op.drop_index(
        "ix_review_items_user_key_next_review_date",
        table_name="review_items",
    )
    op.drop_index("ix_review_items_next_review_date", table_name="review_items")
    op.drop_index("ix_review_items_item_type", table_name="review_items")
    op.drop_index("ix_review_items_active", table_name="review_items")
    op.drop_table("review_items")

    op.drop_index("ix_vocabulary_items_user_key", table_name="vocabulary_items")
    op.drop_index(
        "ix_vocabulary_items_source_resource_id",
        table_name="vocabulary_items",
    )
    op.drop_index(
        "ix_vocabulary_items_mastery_status",
        table_name="vocabulary_items",
    )
    op.drop_index("ix_vocabulary_items_learned_on", table_name="vocabulary_items")
    op.drop_index("ix_vocabulary_items_difficulty", table_name="vocabulary_items")
    op.drop_table("vocabulary_items")
