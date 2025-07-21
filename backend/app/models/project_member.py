import uuid
from typing import TYPE_CHECKING

from sqlalchemy import and_, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.project_type import ProjectType
from app.schemas.project_member import Role


if TYPE_CHECKING:
    from .project import Project
    from .user import User


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # User
    member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Polymorphic project
    project_type: Mapped[ProjectType] = mapped_column(
        ENUM(ProjectType, name="project_type_enum"),
        nullable=False,
        default=ProjectType.PROJECT,
        server_default="PROJECT",
    )
    project_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    # TODO: Remove this column after migration
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )

    # Role
    role: Mapped[Role] = mapped_column(
        ENUM(Role, name="member_role"),
        nullable=False,
        default=Role.VIEWER,
        server_default="VIEWER",
    )

    # Constraints
    __table_args__ = (
        # Ensure that a user can only be a member of a project once
        UniqueConstraint(
            "member_id", "project_type", "project_uuid", name="unique_member_project"
        ),
        # Sanity check that the project_type is valid
        CheckConstraint(
            "project_type IN ('PROJECT')",
            name="check_project_type",
        ),
    )

    # Define relationships
    uas_project: Mapped["Project"] = relationship(
        "Project",
        primaryjoin="and_(ProjectMember.project_type == 'PROJECT', ProjectMember.project_uuid == Project.id)",
        foreign_keys="[ProjectMember.project_uuid]",
        back_populates="uas_members",
    )
    member: Mapped["User"] = relationship(back_populates="project_memberships")
    # TODO: Remove this relationship after migration
    project: Mapped["Project"] = relationship(back_populates="members")

    @property
    def target_project(self):
        """
        Returns the actual target object of the polymorphic relationship.
        """
        if self.project_type is ProjectType.PROJECT:
            return self.uas_project
        return self.uas_project

    def __repr__(self) -> str:
        return (
            f"ProjectMember(id={self.id!r}, "
            f"member_id={self.member_id!r}, "
            f"type={self.project_type.value!r}, "
            f"target={self.project_uuid}, "
            f"role={self.role})"
        )
