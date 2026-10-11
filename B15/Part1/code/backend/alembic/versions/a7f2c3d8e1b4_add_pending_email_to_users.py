"""add pending_email to users

Revision ID: a7f2c3d8e1b4
Revises: 4109959ebc3e
Create Date: 2026-03-31 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7f2c3d8e1b4"
down_revision: str | None = "4109959ebc3e"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("pending_email", sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "pending_email")
