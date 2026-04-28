"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-04-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "br_users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(128), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column("created_at", sa.String(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.String(), server_default=sa.func.now()),
    )
    op.create_table(
        "br_bookmarks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False, index=True),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("author", sa.String(128), server_default=""),
        sa.Column("content_preview", sa.Text(), server_default=""),
        sa.Column("category", sa.String(64), server_default=""),
        sa.Column("tags", sa.Text(), server_default="[]"),
        sa.Column("rating", sa.Integer(), server_default="0"),
        sa.Column("metadata", sa.Text(), server_default="{}"),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("created_at", sa.String(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.String(), server_default=sa.func.now()),
    )
    op.create_table(
        "br_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(32), server_default=""),
        sa.Column("target_id", sa.Integer(), server_default="0"),
        sa.Column("details", sa.Text(), server_default="{}"),
        sa.Column("created_at", sa.String(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.String(), server_default=sa.func.now()),
    )
    op.create_table(
        "br_model_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("model_name", sa.String(128), nullable=False, index=True),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("framework", sa.String(64), server_default=""),
        sa.Column("accuracy", sa.Float(), server_default="0.0"),
        sa.Column("dataset_size", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(32), server_default="training"),
        sa.Column("model_path", sa.String(512), server_default=""),
        sa.Column("training_params", sa.Text(), server_default="{}"),
        sa.Column("created_at", sa.String(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.String(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("br_model_versions")
    op.drop_table("br_audit_logs")
    op.drop_table("br_bookmarks")
    op.drop_table("br_users")
