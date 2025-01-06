"""convert geom column to geometry(Geometry,4326)

Revision ID: 9ef9b06ed105
Revises: 4834cb625e90
Create Date: 2025-01-06 22:17:53.405366

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '9ef9b06ed105'
down_revision: str | None = '4834cb625e90'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Change the `geom` column to geometry(Geometry, 4326)
    op.execute("""
        ALTER TABLE vector_layers
        ALTER COLUMN geom TYPE geometry(Geometry, 4326)
        USING geom::geometry(Geometry, 4326);
    """)


def downgrade() -> None:
    # Revert the `geom` column back to generic geometry
    op.execute("""
        ALTER TABLE vector_layers
        ALTER COLUMN geom TYPE geometry
        USING geom::geometry;
    """)
