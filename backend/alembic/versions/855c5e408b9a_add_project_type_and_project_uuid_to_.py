"""add project_type and project_uuid to project_members

Revision ID: 855c5e408b9a
Revises: 45875ccd4674
Create Date: 2025-07-18 14:48:30.695563

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "855c5e408b9a"
down_revision: str | None = "45875ccd4674"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # 1) create the enum type (if it doesn't already exist)
    project_type_enum = postgresql.ENUM("PROJECT", name="project_type_enum")
    project_type_enum.create(op.get_bind(), checkfirst=True)

    # 2) add the new columns as NULLable
    op.add_column(
        "project_members",
        sa.Column(
            "project_type", project_type_enum, nullable=True, server_default="PROJECT"
        ),
    )
    op.add_column(
        "project_members", sa.Column("project_uuid", sa.UUID(), nullable=True)
    )

    # 3) backfill existing rows
    op.execute(
        """
        UPDATE project_members
        SET project_type = 'PROJECT',
            project_uuid = project_id;
        """
    )

    # 4) make the new columns NOT NULL
    op.alter_column("project_members", "project_type", nullable=False)
    op.alter_column("project_members", "project_uuid", nullable=False)

    # 5) swap out the old unique constraint for the new one
    op.drop_constraint(op.f("unique_to_project"), "project_members", type_="unique")
    op.create_unique_constraint(
        "unique_member_project",
        "project_members",
        ["member_id", "project_type", "project_uuid"],
    )


def downgrade() -> None:
    # 1) drop the new unique constraint
    op.drop_constraint("unique_member_project", "project_members", type_="unique")

    # 2) drop the new columns
    op.drop_column("project_members", "project_uuid")
    op.drop_column("project_members", "project_type")

    # 3) drop the enum type
    project_type_enum = postgresql.ENUM("PROJECT", name="project_type_enum")
    project_type_enum.drop(op.get_bind(), checkfirst=True)

    # 4) re-create the old unique constraint
    op.create_unique_constraint(
        op.f("unique_to_project"),
        "project_members",
        ["member_id", "project_id"],
        postgresql_nulls_not_distinct=False,
    )
