"""add s3_url to data_products and raw_data

Revision ID: 786003d898d7
Revises: a7f2c3d8e1b4
Create Date: 2026-04-12 17:57:25.677328

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '786003d898d7'
down_revision: str | None = 'a7f2c3d8e1b4'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column('data_products', sa.Column('s3_url', sa.String(), nullable=True))
    op.add_column('raw_data', sa.Column('s3_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('raw_data', 's3_url')
    op.drop_column('data_products', 's3_url')
