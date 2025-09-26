import uuid
from datetime import date, datetime
from typing import List, TYPE_CHECKING

from datetime import date

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow


if TYPE_CHECKING:
    from .campaign import Campaign
    from .flight import Flight
    from .iforester import IForester
    from .project_like import ProjectLike
    from .location import Location
    from .project_member import ProjectMember
    from .project_module import ProjectModule
    from .team import Team
    from .user import User
    from .vector_layer import VectorLayer


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    planting_date: Mapped[date] = mapped_column(Date, nullable=True)
    harvest_date: Mapped[date] = mapped_column(Date, nullable=True)
    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )
    deactivated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    members: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="uas_project",
        cascade="all, delete-orphan",
        primaryjoin="and_(ProjectMember.project_type == 'PROJECT', ProjectMember.project_uuid == Project.id)",
        foreign_keys="[ProjectMember.project_uuid]",
    )
    modules: Mapped[List["ProjectModule"]] = relationship(back_populates="project")
    location: Mapped["Location"] = relationship(back_populates="project")
    owner: Mapped["User"] = relationship(back_populates="projects")
    team: Mapped["Team"] = relationship(back_populates="projects")

    campaigns: Mapped[List["Campaign"]] = relationship(
        back_populates="project", cascade="all, delete"
    )
    likes: Mapped[List["ProjectLike"]] = relationship(
        back_populates="project", cascade="all, delete"
    )
    flights: Mapped[List["Flight"]] = relationship(
        back_populates="project", cascade="all, delete"
    )
    iforester: Mapped[List["IForester"]] = relationship(
        back_populates="project", cascade="all, delete"
    )
    vector_layer: Mapped[List["VectorLayer"]] = relationship(
        back_populates="project", cascade="all, delete"
    )

    def __repr__(self) -> str:
        return (
            f"Project(id={self.id!r}, title={self.title!r}, "
            f"description={self.description!r}, "
            f"planting_date={self.planting_date!r}, "
            f"harvest_date={self.harvest_date!r}, owner_id={self.owner_id!r}, "
            f"team_id={self.team_id!r})"
        )
