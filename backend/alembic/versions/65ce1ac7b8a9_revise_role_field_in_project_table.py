"""revise role field in project table

Revision ID: 65ce1ac7b8a9
Revises: 696cde09bec5
Create Date: 2025-03-19 13:44:04.146655

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "65ce1ac7b8a9"
down_revision: str | None = "696cde09bec5"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # First, drop the default
    op.execute("ALTER TABLE project_members ALTER COLUMN role DROP DEFAULT")

    # Then convert the column type including existing values
    op.execute(
        "ALTER TABLE project_members ALTER COLUMN role TYPE member_role USING upper(role)::member_role"
    )

    # Finally, set the new default with the correct type
    op.execute(
        "ALTER TABLE project_members ALTER COLUMN role SET DEFAULT 'VIEWER'::member_role"
    )


def downgrade() -> None:
    # First drop the enum default
    op.execute("ALTER TABLE project_members ALTER COLUMN role DROP DEFAULT")

    # Convert enum values back to strings
    op.execute(
        "ALTER TABLE project_members ALTER COLUMN role TYPE varchar(10) USING role::text"
    )

    # Restore the original default
    op.execute("ALTER TABLE project_members ALTER COLUMN role SET DEFAULT 'viewer'")
