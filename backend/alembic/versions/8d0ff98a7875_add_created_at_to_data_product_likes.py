"""add created_at to data product likes

Revision ID: 8d0ff98a7875
Revises: f7cd65434957
Create Date: 2026-06-20 03:14:34.971895

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d0ff98a7875'
down_revision: str | None = 'f7cd65434957'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column('data_product_likes', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"), nullable=False))


def downgrade() -> None:
    op.drop_column('data_product_likes', 'created_at')
