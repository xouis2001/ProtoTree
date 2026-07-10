"""keep protocol updated_at default for postgres inserts

Revision ID: 20260708_0007
Revises: 20260707_0006
Create Date: 2026-07-08
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260708_0007"
down_revision: str | None = "20260707_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("protocols", "updated_at", server_default=sa.text("now()"), existing_type=sa.DateTime(timezone=True), existing_nullable=False)


def downgrade() -> None:
    op.alter_column("protocols", "updated_at", server_default=None, existing_type=sa.DateTime(timezone=True), existing_nullable=False)
