"""add resource tables and protocol updated timestamp

Revision ID: 20260707_0006
Revises: 20260625_0005
Create Date: 2026-07-07
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260707_0006"
down_revision: str | None = "20260625_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("protocols", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))

    op.create_table(
        "image_macro_resources",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("author_name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_image_macro_resources_author_id"), "image_macro_resources", ["author_id"], unique=False)

    op.create_table(
        "analysis_tool_resources",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("author_name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_tool_resources_author_id"), "analysis_tool_resources", ["author_id"], unique=False)

    op.create_table(
        "agent_skill_resources",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_model", sa.String(length=120), nullable=False),
        sa.Column("source_agent", sa.String(length=120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("author_name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_skill_resources_author_id"), "agent_skill_resources", ["author_id"], unique=False)

    op.create_table(
        "commercial_protocol_resources",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("manufacturer", sa.String(length=255), nullable=False),
        sa.Column("catalog_no", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("author_name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_commercial_protocol_resources_author_id"), "commercial_protocol_resources", ["author_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_commercial_protocol_resources_author_id"), table_name="commercial_protocol_resources")
    op.drop_table("commercial_protocol_resources")
    op.drop_index(op.f("ix_agent_skill_resources_author_id"), table_name="agent_skill_resources")
    op.drop_table("agent_skill_resources")
    op.drop_index(op.f("ix_analysis_tool_resources_author_id"), table_name="analysis_tool_resources")
    op.drop_table("analysis_tool_resources")
    op.drop_index(op.f("ix_image_macro_resources_author_id"), table_name="image_macro_resources")
    op.drop_table("image_macro_resources")
    op.drop_column("protocols", "updated_at")
