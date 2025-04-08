import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base_class import Base
from app.schemas.project_member import Role


if TYPE_CHECKING:
    from .project import Project
    from .user import User


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role: Mapped[Role] = mapped_column(
        ENUM(Role, name="member_role"),
        nullable=False,
        default=Role.VIEWER,
        server_default="VIEWER",
    )
    member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )

    # Define relationships
    member: Mapped["User"] = relationship(back_populates="project_memberships")
    project: Mapped["Project"] = relationship(back_populates="members")

    # Ensure that a user can only be a member of a project once
    __table_args__ = (
        UniqueConstraint("member_id", "project_id", name="unique_to_project"),
    )

    def __repr__(self) -> str:
        return (
            f"ProjectMember(id={self.id!r}, role={self.role}, "
            f"member_id={self.member_id!r}, project_id={self.project_id})"
        )
