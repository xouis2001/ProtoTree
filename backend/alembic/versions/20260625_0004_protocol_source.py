"""add protocol source

Revision ID: 20260625_0004
Revises: 20260622_0003
Create Date: 2026-06-25
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260625_0004"
down_revision: str | None = "20260622_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    protocol_source = postgresql.ENUM("user", "base", name="protocol_source", create_type=False)
    protocol_source.create(op.get_bind(), checkfirst=True)
    op.add_column("protocols", sa.Column("source", protocol_source, nullable=False, server_default="user"))
    op.create_index(op.f("ix_protocols_source"), "protocols", ["source"], unique=False)
    op.alter_column("protocols", "source", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_protocols_source"), table_name="protocols")
    op.drop_column("protocols", "source")
    sa.Enum(name="protocol_source").drop(op.get_bind(), checkfirst=True)
