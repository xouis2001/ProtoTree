"""add taxonomy tables

Revision ID: 20260625_0005
Revises: 20260625_0004
Create Date: 2026-06-25
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260625_0005"
down_revision: str | None = "20260625_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    taxonomy_source = postgresql.ENUM("official", "user", "community", name="taxonomy_source", create_type=False)
    taxonomy_status = postgresql.ENUM("active", "merged", "disabled", name="taxonomy_status", create_type=False)
    taxonomy_source.create(op.get_bind(), checkfirst=True)
    taxonomy_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "protocol_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("color", sa.String(length=40), nullable=False, server_default="#2563eb"),
        sa.Column("source", taxonomy_source, nullable=False),
        sa.Column("status", taxonomy_status, nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_protocol_categories_id"), "protocol_categories", ["id"], unique=False)
    op.create_index(op.f("ix_protocol_categories_name"), "protocol_categories", ["name"], unique=False)

    op.create_table(
        "protocol_tag_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("normalized_name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("source", taxonomy_source, nullable=False),
        sa.Column("status", taxonomy_status, nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("merged_into_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["protocol_categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["merged_into_id"], ["protocol_tag_groups.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "normalized_name", name="uq_protocol_tag_group_category_name"),
    )
    op.create_index(op.f("ix_protocol_tag_groups_category_id"), "protocol_tag_groups", ["category_id"], unique=False)
    op.create_index(op.f("ix_protocol_tag_groups_id"), "protocol_tag_groups", ["id"], unique=False)
    op.create_index(op.f("ix_protocol_tag_groups_name"), "protocol_tag_groups", ["name"], unique=False)
    op.create_index(op.f("ix_protocol_tag_groups_normalized_name"), "protocol_tag_groups", ["normalized_name"], unique=False)

    op.create_table(
        "protocol_tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("tag_group_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("normalized_name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("source", taxonomy_source, nullable=False),
        sa.Column("status", taxonomy_status, nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("merged_into_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["protocol_categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["merged_into_id"], ["protocol_tags.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tag_group_id"], ["protocol_tag_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "tag_group_id", "normalized_name", name="uq_protocol_tag_group_name"),
    )
    op.create_index(op.f("ix_protocol_tags_category_id"), "protocol_tags", ["category_id"], unique=False)
    op.create_index(op.f("ix_protocol_tags_id"), "protocol_tags", ["id"], unique=False)
    op.create_index(op.f("ix_protocol_tags_name"), "protocol_tags", ["name"], unique=False)
    op.create_index(op.f("ix_protocol_tags_normalized_name"), "protocol_tags", ["normalized_name"], unique=False)
    op.create_index(op.f("ix_protocol_tags_tag_group_id"), "protocol_tags", ["tag_group_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_protocol_tags_tag_group_id"), table_name="protocol_tags")
    op.drop_index(op.f("ix_protocol_tags_normalized_name"), table_name="protocol_tags")
    op.drop_index(op.f("ix_protocol_tags_name"), table_name="protocol_tags")
    op.drop_index(op.f("ix_protocol_tags_id"), table_name="protocol_tags")
    op.drop_index(op.f("ix_protocol_tags_category_id"), table_name="protocol_tags")
    op.drop_table("protocol_tags")
    op.drop_index(op.f("ix_protocol_tag_groups_normalized_name"), table_name="protocol_tag_groups")
    op.drop_index(op.f("ix_protocol_tag_groups_name"), table_name="protocol_tag_groups")
    op.drop_index(op.f("ix_protocol_tag_groups_id"), table_name="protocol_tag_groups")
    op.drop_index(op.f("ix_protocol_tag_groups_category_id"), table_name="protocol_tag_groups")
    op.drop_table("protocol_tag_groups")
    op.drop_index(op.f("ix_protocol_categories_name"), table_name="protocol_categories")
    op.drop_index(op.f("ix_protocol_categories_id"), table_name="protocol_categories")
    op.drop_table("protocol_categories")
    sa.Enum(name="taxonomy_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="taxonomy_source").drop(op.get_bind(), checkfirst=True)
