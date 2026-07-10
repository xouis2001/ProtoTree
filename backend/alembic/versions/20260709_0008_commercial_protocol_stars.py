"""add commercial protocol stars

Revision ID: 20260709_0008
Revises: 20260708_0008
Create Date: 2026-07-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260709_0008"
down_revision: str | None = "20260708_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "commercial_protocol_stars",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("commercial_protocol_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["commercial_protocol_id"], ["commercial_protocol_resources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("commercial_protocol_id", "user_id", name="uq_commercial_protocol_star_user"),
    )
    op.create_index(op.f("ix_commercial_protocol_stars_id"), "commercial_protocol_stars", ["id"], unique=False)
    op.create_index(op.f("ix_commercial_protocol_stars_commercial_protocol_id"), "commercial_protocol_stars", ["commercial_protocol_id"], unique=False)
    op.create_index(op.f("ix_commercial_protocol_stars_user_id"), "commercial_protocol_stars", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_commercial_protocol_stars_user_id"), table_name="commercial_protocol_stars")
    op.drop_index(op.f("ix_commercial_protocol_stars_commercial_protocol_id"), table_name="commercial_protocol_stars")
    op.drop_index(op.f("ix_commercial_protocol_stars_id"), table_name="commercial_protocol_stars")
    op.drop_table("commercial_protocol_stars")
