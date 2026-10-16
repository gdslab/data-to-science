"""add name and scopes to api_keys

Revision ID: b31cf1dcef74
Revises: db4a6ae51d8b
Create Date: 2026-09-24 17:27:03.197045

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "b31cf1dcef74"
down_revision: str | None = "db4a6ae51d8b"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("api_keys", sa.Column("name", sa.String(length=64), nullable=True))
    op.add_column(
        "api_keys",
        sa.Column(
            "scopes",
            postgresql.ARRAY(sa.String(length=16)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
    )
    # existing keys keep full access so current integrations continue to work
    op.execute(
        "UPDATE api_keys SET scopes = ARRAY['read', 'create', 'update', 'delete']"
    )


def downgrade() -> None:
    op.drop_column("api_keys", "scopes")
    op.drop_column("api_keys", "name")
