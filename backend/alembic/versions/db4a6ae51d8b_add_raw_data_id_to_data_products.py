"""add raw_data_id to data_products

Revision ID: db4a6ae51d8b
Revises: 8a820e756cbd
Create Date: 2026-07-24 14:54:31.660169

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "db4a6ae51d8b"
down_revision: str | None = "8a820e756cbd"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Source raw data upload a data product was derived from by the external
    # image processing service. SET NULL on delete so raw data cleanup jobs can
    # hard-delete deactivated raw data without hitting FK violations.
    op.add_column("data_products", sa.Column("raw_data_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_data_products_raw_data",
        "data_products",
        "raw_data",
        ["raw_data_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_data_products_raw_data", "data_products", type_="foreignkey")
    op.drop_column("data_products", "raw_data_id")
