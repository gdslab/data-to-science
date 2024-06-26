"""drop center_x and center_y requirement for location objects

Revision ID: 3bf88d6f9581
Revises: 314a512083ba
Create Date: 2024-06-05 01:05:43.346876

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3bf88d6f9581'
down_revision: str | None = '314a512083ba'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('locations', 'center_y')
    op.drop_column('locations', 'center_x')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('locations', sa.Column('center_x', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.add_column('locations', sa.Column('center_y', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
