"""ensure commercial protocol stars table exists

Revision ID: 20260709_0009
Revises: 20260709_0008
Create Date: 2026-07-09 19:30:00.000000
"""

from alembic import op


revision = "20260709_0009"
down_revision = "20260709_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS commercial_protocol_stars (
            id SERIAL PRIMARY KEY,
            commercial_protocol_id VARCHAR(32) NOT NULL REFERENCES commercial_protocol_resources(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            CONSTRAINT uq_commercial_protocol_star_user UNIQUE (commercial_protocol_id, user_id)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_commercial_protocol_stars_id ON commercial_protocol_stars (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commercial_protocol_stars_commercial_protocol_id ON commercial_protocol_stars (commercial_protocol_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commercial_protocol_stars_user_id ON commercial_protocol_stars (user_id)")


def downgrade() -> None:
    # The table is owned by revision 20260709_0008; this revision is a
    # production repair for environments stamped before the file was restored.
    pass
