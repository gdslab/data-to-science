"""add revoked_at to refresh_tokens

Revision ID: f7cd65434957
Revises: fa8f9fed28e9
Create Date: 2026-06-17 20:07:00.583021

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7cd65434957'
down_revision: str | None = 'fa8f9fed28e9'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column('refresh_tokens', sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('refresh_tokens', 'revoked_at')
