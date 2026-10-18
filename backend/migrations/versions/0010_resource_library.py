"""Add personal resource management and library state.

Revision ID: 0010_resource_library
Revises: 0009_practice_notebook
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0010_resource_library"
down_revision: str | None = "0009_practice_notebook"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("learning_resources") as batch_op:
        batch_op.add_column(
            sa.Column("owner_user_key", sa.String(length=120), nullable=True)
        )
        batch_op.add_column(
            sa.Column("description", sa.Text(), server_default="", nullable=False)
        )
        batch_op.add_column(
            sa.Column("content_text", sa.Text(), server_default="", nullable=False)
        )
        batch_op.add_column(
            sa.Column("transcript", sa.Text(), server_default="", nullable=False)
        )
        batch_op.add_column(
            sa.Column("notes", sa.Text(), server_default="", nullable=False)
        )
        batch_op.create_index(
            "ix_learning_resources_owner_user_key", ["owner_user_key"]
        )

    op.create_table(
        "resource_user_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_key", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("favorite", sa.Boolean(), nullable=False),
        sa.Column("saved_for_later", sa.Boolean(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["resource_id"], ["learning_resources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_key", "resource_id"),
    )
    op.create_index(
        "ix_resource_user_states_user_key", "resource_user_states", ["user_key"]
    )
    op.create_index(
        "ix_resource_user_states_resource_id", "resource_user_states", ["resource_id"]
    )
    op.create_index(
        "ix_resource_user_states_favorite", "resource_user_states", ["favorite"]
    )
    op.create_index(
        "ix_resource_user_states_saved_for_later",
        "resource_user_states",
        ["saved_for_later"],
    )
    op.create_index(
        "ix_resource_user_states_archived_at",
        "resource_user_states",
        ["archived_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_resource_user_states_archived_at", table_name="resource_user_states"
    )
    op.drop_index(
        "ix_resource_user_states_saved_for_later", table_name="resource_user_states"
    )
    op.drop_index("ix_resource_user_states_favorite", table_name="resource_user_states")
    op.drop_index(
        "ix_resource_user_states_resource_id", table_name="resource_user_states"
    )
    op.drop_index("ix_resource_user_states_user_key", table_name="resource_user_states")
    op.drop_table("resource_user_states")

    with op.batch_alter_table("learning_resources") as batch_op:
        batch_op.drop_index("ix_learning_resources_owner_user_key")
        batch_op.drop_column("notes")
        batch_op.drop_column("transcript")
        batch_op.drop_column("content_text")
        batch_op.drop_column("description")
        batch_op.drop_column("owner_user_key")
