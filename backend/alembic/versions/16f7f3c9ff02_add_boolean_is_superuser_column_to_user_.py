"""add boolean is_superuser column to user model

Revision ID: 16f7f3c9ff02
Revises: b5bd06a37a63
Create Date: 2023-06-18 13:59:19.947238

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16f7f3c9ff02'
down_revision: str | None = 'b5bd06a37a63'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'is_superuser')
    # ### end Alembic commands ###