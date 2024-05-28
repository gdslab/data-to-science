import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from datetime import date

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .campaign import Campaign
    from .flight import Flight
    from .location import Location
    from .project_member import ProjectMember
    from .team import Team
    from .user import User
    from .vector_layer import VectorLayer


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(300))
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
    deactivated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete"
    )

    location: Mapped["Location"] = relationship(back_populates="project")
    owner: Mapped["User"] = relationship(back_populates="projects")
    team: Mapped["Team"] = relationship(back_populates="projects")

    campaigns: Mapped[list["Campaign"]] = relationship(
        back_populates="project", cascade="all, delete"
    )
    flights: Mapped[list["Flight"]] = relationship(
        back_populates="project", cascade="all, delete"
    )
    vector_layer: Mapped[list["VectorLayer"]] = relationship(
        back_populates="project", cascade="all, delete"
    )

    def __repr__(self) -> str:
        return (
            f"Project(id={self.id!r}, title={self.title!r}, "
            f"description={self.description!r} "
            f"planting_date={self.planting_date!r}, "
            f"harvest_date={self.harvest_date!r}, owner_id={self.owner_id!r}, "
            f"team_id={self.team_id!r})"
        )
