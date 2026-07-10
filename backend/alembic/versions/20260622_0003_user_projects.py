"""add user projects

Revision ID: 20260622_0003
Revises: 20260618_0001
Create Date: 2026-06-22
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260622_0003"
down_revision: str | None = "20260618_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("projects", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"))
    op.alter_column("users", "projects", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "projects")
