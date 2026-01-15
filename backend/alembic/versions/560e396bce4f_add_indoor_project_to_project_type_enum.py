"""add indoor_project to project_type enum and remove project_id column

Revision ID: 560e396bce4f
Revises: 9953a4575624
Create Date: 2025-07-25 18:25:12.477297

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "560e396bce4f"
down_revision: str | None = "9953a4575624"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # 1) Add INDOOR_PROJECT to the existing enum
    op.execute("ALTER TYPE project_type_enum ADD VALUE 'INDOOR_PROJECT'")

    # 2) Remove the project_id column (it's problematic for polymorphic relationships)
    op.drop_column("project_members", "project_id")


def downgrade() -> None:
    # WARNING: This downgrade removes the INDOOR_PROJECT enum value
    # Make sure no records use INDOOR_PROJECT before running this!

    # 1) Re-add the project_id column (simplified - just for regular projects)
    op.add_column("project_members", sa.Column("project_id", sa.UUID(), nullable=True))

    # 2) Backfill project_id for existing PROJECT type records only
    op.execute(
        """
        UPDATE project_members
        SET project_id = project_uuid
        WHERE project_type = 'PROJECT';
        """
    )

    # 3) Make project_id NOT NULL for PROJECT type records only
    op.execute(
        """
        ALTER TABLE project_members 
        ADD CONSTRAINT check_project_id_not_null_for_projects 
        CHECK (project_type != 'PROJECT' OR project_id IS NOT NULL);
        """
    )

    # 4) Re-create the old unique constraint
    op.create_unique_constraint(
        "unique_to_project",
        "project_members",
        ["member_id", "project_id"],
        postgresql_nulls_not_distinct=False,
    )

    # 5) Remove INDOOR_PROJECT from enum by recreating it
    # First, create a new enum with only PROJECT
    op.execute("CREATE TYPE project_type_enum_new AS ENUM ('PROJECT')")

    # Drop the default value before changing the type
    op.execute("ALTER TABLE project_members ALTER COLUMN project_type DROP DEFAULT")

    # Update the column to use the new enum
    op.execute(
        "ALTER TABLE project_members ALTER COLUMN project_type TYPE project_type_enum_new USING project_type::text::project_type_enum_new"
    )

    # Recreate the default value
    op.execute(
        "ALTER TABLE project_members ALTER COLUMN project_type SET DEFAULT 'PROJECT'::project_type_enum_new"
    )

    # Drop the old enum
    op.execute("DROP TYPE project_type_enum")

    # Rename the new enum to the original name
    op.execute("ALTER TYPE project_type_enum_new RENAME TO project_type_enum")
