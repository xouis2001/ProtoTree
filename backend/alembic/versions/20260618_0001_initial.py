"""initial schema

Revision ID: 20260618_0001
Revises:
Create Date: 2026-06-18
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260618_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    user_role = postgresql.ENUM("PI", "student", name="user_role", create_type=False)
    protocol_visibility = postgresql.ENUM("public", "private", name="protocol_visibility", create_type=False)
    contribution_event_type = postgresql.ENUM(
        "create_protocol",
        "fork_protocol",
        "protocol_forked_by_other",
        "update_protocol",
        "add_pitfall",
        "add_comment",
        "receive_star",
        name="contribution_event_type",
        create_type=False,
    )
    user_role.create(op.get_bind(), checkfirst=True)
    protocol_visibility.create(op.get_bind(), checkfirst=True)
    contribution_event_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("avatar", sa.String(length=80), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("contribution_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "protocol_folders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["protocol_folders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "parent_id", "name", name="uq_protocol_folder_sibling_name"),
    )
    op.create_index(op.f("ix_protocol_folders_id"), "protocol_folders", ["id"], unique=False)
    op.create_index(op.f("ix_protocol_folders_owner_id"), "protocol_folders", ["owner_id"], unique=False)
    op.create_index(op.f("ix_protocol_folders_parent_id"), "protocol_folders", ["parent_id"], unique=False)

    op.create_table(
        "protocols",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("root_id", sa.Integer(), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=True),
        sa.Column("visibility", protocol_visibility, nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("structured", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("version_label", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["folder_id"], ["protocol_folders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_id"], ["protocols.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["root_id"], ["protocols.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_protocols_author_id"), "protocols", ["author_id"], unique=False)
    op.create_index(op.f("ix_protocols_folder_id"), "protocols", ["folder_id"], unique=False)
    op.create_index(op.f("ix_protocols_id"), "protocols", ["id"], unique=False)
    op.create_index(op.f("ix_protocols_parent_id"), "protocols", ["parent_id"], unique=False)
    op.create_index(op.f("ix_protocols_root_id"), "protocols", ["root_id"], unique=False)
    op.create_index(op.f("ix_protocols_title"), "protocols", ["title"], unique=False)

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("protocol_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["protocol_id"], ["protocols.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comments_author_id"), "comments", ["author_id"], unique=False)
    op.create_index(op.f("ix_comments_id"), "comments", ["id"], unique=False)
    op.create_index(op.f("ix_comments_protocol_id"), "comments", ["protocol_id"], unique=False)
    op.create_index(op.f("ix_comments_step_order"), "comments", ["step_order"], unique=False)

    op.create_table(
        "contribution_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", contribution_event_type, nullable=False),
        sa.Column("score_delta", sa.Integer(), nullable=False),
        sa.Column("protocol_id", sa.Integer(), nullable=True),
        sa.Column("related_protocol_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["protocol_id"], ["protocols.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["related_protocol_id"], ["protocols.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contribution_events_event_type"), "contribution_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_contribution_events_id"), "contribution_events", ["id"], unique=False)
    op.create_index(op.f("ix_contribution_events_protocol_id"), "contribution_events", ["protocol_id"], unique=False)
    op.create_index(op.f("ix_contribution_events_related_protocol_id"), "contribution_events", ["related_protocol_id"], unique=False)
    op.create_index(op.f("ix_contribution_events_user_id"), "contribution_events", ["user_id"], unique=False)

    op.create_table(
        "pitfalls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("protocol_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["protocol_id"], ["protocols.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pitfalls_author_id"), "pitfalls", ["author_id"], unique=False)
    op.create_index(op.f("ix_pitfalls_id"), "pitfalls", ["id"], unique=False)
    op.create_index(op.f("ix_pitfalls_protocol_id"), "pitfalls", ["protocol_id"], unique=False)
    op.create_index(op.f("ix_pitfalls_step_order"), "pitfalls", ["step_order"], unique=False)

    op.create_table(
        "protocol_stars",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("protocol_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["protocol_id"], ["protocols.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("protocol_id", "user_id", name="uq_protocol_star_user"),
    )
    op.create_index(op.f("ix_protocol_stars_id"), "protocol_stars", ["id"], unique=False)
    op.create_index(op.f("ix_protocol_stars_protocol_id"), "protocol_stars", ["protocol_id"], unique=False)
    op.create_index(op.f("ix_protocol_stars_user_id"), "protocol_stars", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_protocol_stars_user_id"), table_name="protocol_stars")
    op.drop_index(op.f("ix_protocol_stars_protocol_id"), table_name="protocol_stars")
    op.drop_index(op.f("ix_protocol_stars_id"), table_name="protocol_stars")
    op.drop_table("protocol_stars")
    op.drop_index(op.f("ix_pitfalls_step_order"), table_name="pitfalls")
    op.drop_index(op.f("ix_pitfalls_protocol_id"), table_name="pitfalls")
    op.drop_index(op.f("ix_pitfalls_id"), table_name="pitfalls")
    op.drop_index(op.f("ix_pitfalls_author_id"), table_name="pitfalls")
    op.drop_table("pitfalls")
    op.drop_index(op.f("ix_contribution_events_user_id"), table_name="contribution_events")
    op.drop_index(op.f("ix_contribution_events_related_protocol_id"), table_name="contribution_events")
    op.drop_index(op.f("ix_contribution_events_protocol_id"), table_name="contribution_events")
    op.drop_index(op.f("ix_contribution_events_id"), table_name="contribution_events")
    op.drop_index(op.f("ix_contribution_events_event_type"), table_name="contribution_events")
    op.drop_table("contribution_events")
    op.drop_index(op.f("ix_comments_step_order"), table_name="comments")
    op.drop_index(op.f("ix_comments_protocol_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_author_id"), table_name="comments")
    op.drop_table("comments")
    op.drop_index(op.f("ix_protocols_title"), table_name="protocols")
    op.drop_index(op.f("ix_protocols_root_id"), table_name="protocols")
    op.drop_index(op.f("ix_protocols_parent_id"), table_name="protocols")
    op.drop_index(op.f("ix_protocols_id"), table_name="protocols")
    op.drop_index(op.f("ix_protocols_folder_id"), table_name="protocols")
    op.drop_index(op.f("ix_protocols_author_id"), table_name="protocols")
    op.drop_table("protocols")
    op.drop_index(op.f("ix_protocol_folders_parent_id"), table_name="protocol_folders")
    op.drop_index(op.f("ix_protocol_folders_owner_id"), table_name="protocol_folders")
    op.drop_index(op.f("ix_protocol_folders_id"), table_name="protocol_folders")
    op.drop_table("protocol_folders")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    sa.Enum(name="contribution_event_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="protocol_visibility").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
