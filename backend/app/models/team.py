import uuid
from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .indoor_project import IndoorProject
    from .project import Project
    from .team_extension import TeamExtension
    from .team_member import TeamMember
    from .user import User


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    extensions: Mapped[List["TeamExtension"]] = relationship(
        back_populates="team", cascade="all, delete", lazy="joined"
    )
    members: Mapped[List["TeamMember"]] = relationship(
        back_populates="team", cascade="all, delete"
    )
    owner: Mapped["User"] = relationship(back_populates="teams")
    projects: Mapped[List["Project"]] = relationship(back_populates="team")
    indoor_projects: Mapped[List["IndoorProject"]] = relationship(back_populates="team")

    def __repr__(self) -> str:
        return (
            f"Team(id={self.id!r}, title={self.title!r}, "
            f"description={self.description!r}, owner_id={self.owner_id!r})"
        )
