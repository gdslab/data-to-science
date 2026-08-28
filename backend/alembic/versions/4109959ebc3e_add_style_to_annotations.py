"""add style to annotations

Revision ID: 4109959ebc3e
Revises: 88583aa69cf0
Create Date: 2026-03-20 00:33:00.720137

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "4109959ebc3e"
down_revision: str | None = "88583aa69cf0"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "annotations",
        sa.Column("style", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("annotations", "style")
