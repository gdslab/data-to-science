import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base_class import Base

if TYPE_CHECKING:
    from .project import Project
    from .user import User


class ProjectLike(Base):
    __tablename__ = "project_likes"

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="project_likes")
    project: Mapped["Project"] = relationship(back_populates="likes")

    # Ensure that a user can only like a project once
    __table_args__ = (
        UniqueConstraint(
            "user_id", "project_id", name="like_unique_to_project_and_user"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"ProjectLike(id={self.id}, user_id={self.user_id}, "
            f"project_id={self.project_id})"
        )
