import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base_class import Base


if TYPE_CHECKING:
    from .project import Project
    from .user import User


ROLES = ["owner", "manager", "viewer"]


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False, default="viewer")
    member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("member_id", "project_id", name="unique_to_project"),
    )

    member: Mapped["User"] = relationship(back_populates="project_memberships")
    project: Mapped["Project"] = relationship(back_populates="members")

    def __repr__(self) -> str:
        return (
            f"ProjectMember(id={self.id!r}, "
            f"member_id={self.member_id!r}, "
            f"role={self.role!r})"
        )
