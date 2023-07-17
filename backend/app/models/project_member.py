import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .project import Project
    from .user import User


ROLES = ["Standard", "Manager"]


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role: Mapped[enumerate] = mapped_column(
        ENUM(*ROLES, name="project_role_type"), default="Standard", nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )

    member: Mapped["User"] = relationship(back_populates="team_memberships")
    project: Mapped["Project"] = relationship(back_populates="members")

    def __repr__(self) -> str:
        return (
            f"ProjectMember(id={self.id!r}, role={self.role!r}, "
            f"member_id={self.member_id!r})"
        )
