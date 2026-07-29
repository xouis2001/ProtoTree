"""add onboarding completion and email outbox

Revision ID: 20260727_0011
Revises: 20260723_0010
Create Date: 2026-07-27
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260727_0011"
down_revision: str | None = "20260723_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "email_outbox",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_key", sa.String(length=255), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("template", sa.String(length=80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_key", "recipient", name="uq_email_outbox_event_recipient"),
    )
    op.create_index(op.f("ix_email_outbox_event_key"), "email_outbox", ["event_key"], unique=False)
    op.create_index(op.f("ix_email_outbox_recipient"), "email_outbox", ["recipient"], unique=False)
    op.create_index(op.f("ix_email_outbox_status"), "email_outbox", ["status"], unique=False)
    op.create_index(op.f("ix_email_outbox_next_attempt_at"), "email_outbox", ["next_attempt_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_email_outbox_next_attempt_at"), table_name="email_outbox")
    op.drop_index(op.f("ix_email_outbox_status"), table_name="email_outbox")
    op.drop_index(op.f("ix_email_outbox_recipient"), table_name="email_outbox")
    op.drop_index(op.f("ix_email_outbox_event_key"), table_name="email_outbox")
    op.drop_table("email_outbox")
    op.drop_column("users", "submitted_at")
    op.drop_column("users", "onboarding_completed")
