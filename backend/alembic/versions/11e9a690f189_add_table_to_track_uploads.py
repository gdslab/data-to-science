"""add table to track uploads

Revision ID: 11e9a690f189
Revises: 2560a312a401
Create Date: 2024-05-01 17:49:34.791378

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11e9a690f189'
down_revision: str | None = '2560a312a401'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('uploads',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('upload_id', sa.String(length=32), nullable=False),
    sa.Column('is_uploading', sa.Boolean(), nullable=False),
    sa.Column('last_updated_at', sa.DateTime(), server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('uploads')
    # ### end Alembic commands ###