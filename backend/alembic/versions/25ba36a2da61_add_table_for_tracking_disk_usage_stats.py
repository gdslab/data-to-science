"""add table for tracking disk usage stats

Revision ID: 25ba36a2da61
Revises: 30430c513b9b
Create Date: 2025-02-17 16:14:18.201815

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '25ba36a2da61'
down_revision: str | None = '30430c513b9b'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('disk_usage_stats',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('disk_free', sa.BigInteger(), nullable=False),
    sa.Column('disk_total', sa.BigInteger(), nullable=False),
    sa.Column('disk_used', sa.BigInteger(), nullable=False),
    sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('disk_usage_stats')
    # ### end Alembic commands ###
