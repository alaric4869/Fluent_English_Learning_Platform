"""Add listening sentences, speaking records and notebook notes.

Revision ID: 0009_practice_notebook
Revises: 0008_vocabulary_review
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0009_practice_notebook"
down_revision: str | None = "0008_vocabulary_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_sentences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("sentence", sa.Text(), nullable=False),
        sa.Column("meaning", sa.Text(), nullable=False),
        sa.Column("learned_on", sa.Date(), nullable=False),
        sa.Column("practice_status", sa.String(length=40), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("source_resource_id", sa.Integer(), nullable=True),
        sa.Column("source_context", sa.Text(), nullable=False),
        sa.Column("favorite", sa.Boolean(), nullable=False),
        sa.Column("saved_for_later", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_resource_id"], ["learning_resources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_sentences_user_key", "saved_sentences", ["user_key"])
    op.create_index("ix_saved_sentences_learned_on", "saved_sentences", ["learned_on"])
    op.create_index(
        "ix_saved_sentences_practice_status", "saved_sentences", ["practice_status"]
    )
    op.create_index(
        "ix_saved_sentences_source_resource_id",
        "saved_sentences",
        ["source_resource_id"],
    )

    op.create_table(
        "speaking_retelling_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("written_outline", sa.Text(), nullable=False),
        sa.Column("intended_vocabulary", sa.JSON(), nullable=False),
        sa.Column("mistakes", sa.Text(), nullable=False),
        sa.Column("improved_version", sa.Text(), nullable=False),
        sa.Column("practice_status", sa.String(length=40), nullable=False),
        sa.Column("source_resource_id", sa.Integer(), nullable=True),
        sa.Column("source_context", sa.Text(), nullable=False),
        sa.Column("voice_recording_reference", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_resource_id"], ["learning_resources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_speaking_retelling_records_user_key",
        "speaking_retelling_records",
        ["user_key"],
    )
    op.create_index(
        "ix_speaking_retelling_records_practice_status",
        "speaking_retelling_records",
        ["practice_status"],
    )
    op.create_index(
        "ix_speaking_retelling_records_source_resource_id",
        "speaking_retelling_records",
        ["source_resource_id"],
    )

    op.create_table(
        "notebook_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("note_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_resource_id", sa.Integer(), nullable=True),
        sa.Column("source_context", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("favorite", sa.Boolean(), nullable=False),
        sa.Column("saved_for_later", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_resource_id"], ["learning_resources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notebook_notes_user_key", "notebook_notes", ["user_key"])
    op.create_index("ix_notebook_notes_note_type", "notebook_notes", ["note_type"])
    op.create_index(
        "ix_notebook_notes_source_resource_id",
        "notebook_notes",
        ["source_resource_id"],
    )

    with op.batch_alter_table("review_items", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("saved_sentence_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("mastery_status", sa.String(length=30), nullable=True))
        batch_op.alter_column("vocabulary_item_id", existing_type=sa.Integer(), nullable=True)
        batch_op.create_foreign_key(
            "fk_review_items_saved_sentence_id",
            "saved_sentences",
            ["saved_sentence_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_review_items_saved_sentence_id", ["saved_sentence_id"]
        )
        batch_op.create_check_constraint(
            "ck_review_items_exactly_one_target",
            "(vocabulary_item_id IS NOT NULL AND saved_sentence_id IS NULL) OR "
            "(vocabulary_item_id IS NULL AND saved_sentence_id IS NOT NULL)",
        )

    op.execute(
        sa.text(
            """
            UPDATE review_items
            SET mastery_status = COALESCE(
                (SELECT vocabulary_items.mastery_status
                 FROM vocabulary_items
                 WHERE vocabulary_items.id = review_items.vocabulary_item_id),
                'new'
            )
            """
        )
    )
    with op.batch_alter_table("review_items", recreate="always") as batch_op:
        batch_op.alter_column(
            "mastery_status",
            existing_type=sa.String(length=30),
            nullable=False,
        )
        batch_op.create_index(
            "ix_review_items_mastery_status", ["mastery_status"], unique=False
        )

    with op.batch_alter_table("vocabulary_items", recreate="always") as batch_op:
        batch_op.drop_index("ix_vocabulary_items_mastery_status")
        batch_op.drop_column("mastery_status")


def downgrade() -> None:
    with op.batch_alter_table("vocabulary_items", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("mastery_status", sa.String(length=30), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE vocabulary_items
            SET mastery_status = COALESCE(
                (SELECT review_items.mastery_status
                 FROM review_items
                 WHERE review_items.vocabulary_item_id = vocabulary_items.id),
                'new'
            )
            """
        )
    )
    with op.batch_alter_table("vocabulary_items", recreate="always") as batch_op:
        batch_op.alter_column(
            "mastery_status",
            existing_type=sa.String(length=30),
            nullable=False,
        )
        batch_op.create_index(
            "ix_vocabulary_items_mastery_status", ["mastery_status"], unique=False
        )

    op.execute(
        sa.text(
            "DELETE FROM review_attempts WHERE review_item_id IN "
            "(SELECT id FROM review_items WHERE saved_sentence_id IS NOT NULL)"
        )
    )
    op.execute(sa.text("DELETE FROM review_items WHERE saved_sentence_id IS NOT NULL"))
    with op.batch_alter_table("review_items", recreate="always") as batch_op:
        batch_op.drop_index("ix_review_items_mastery_status")
        batch_op.drop_constraint(
            "ck_review_items_exactly_one_target", type_="check"
        )
        batch_op.drop_constraint(
            "uq_review_items_saved_sentence_id", type_="unique"
        )
        batch_op.drop_constraint(
            "fk_review_items_saved_sentence_id", type_="foreignkey"
        )
        batch_op.drop_column("saved_sentence_id")
        batch_op.drop_column("mastery_status")
        batch_op.alter_column("vocabulary_item_id", existing_type=sa.Integer(), nullable=False)

    op.drop_index("ix_notebook_notes_source_resource_id", table_name="notebook_notes")
    op.drop_index("ix_notebook_notes_note_type", table_name="notebook_notes")
    op.drop_index("ix_notebook_notes_user_key", table_name="notebook_notes")
    op.drop_table("notebook_notes")

    op.drop_index(
        "ix_speaking_retelling_records_source_resource_id",
        table_name="speaking_retelling_records",
    )
    op.drop_index(
        "ix_speaking_retelling_records_practice_status",
        table_name="speaking_retelling_records",
    )
    op.drop_index(
        "ix_speaking_retelling_records_user_key",
        table_name="speaking_retelling_records",
    )
    op.drop_table("speaking_retelling_records")

    op.drop_index(
        "ix_saved_sentences_source_resource_id", table_name="saved_sentences"
    )
    op.drop_index("ix_saved_sentences_practice_status", table_name="saved_sentences")
    op.drop_index("ix_saved_sentences_learned_on", table_name="saved_sentences")
    op.drop_index("ix_saved_sentences_user_key", table_name="saved_sentences")
    op.drop_table("saved_sentences")
