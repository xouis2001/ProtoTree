"""add user approval workflow fields

Revision ID: 20260723_0010
Revises: 20260709_0009
Create Date: 2026-07-23
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260723_0010"
down_revision: str | None = "20260709_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("approval_status", sa.String(length=20), nullable=False, server_default="approved"))
    op.add_column("users", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("approved_by_id", sa.Integer(), nullable=True))
    op.execute("UPDATE users SET approval_status = 'approved' WHERE approval_status IS NULL")


def downgrade() -> None:
    op.drop_column("users", "approved_by_id")
    op.drop_column("users", "approved_at")
    op.drop_column("users", "approval_status")
