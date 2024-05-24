import uuid
from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import column_property, Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.user import utcnow


if TYPE_CHECKING:
    from .api_key import APIKey
    from .campaign import Campaign
    from .flight import Flight
    from .team import Team
    from .team_member import TeamMember
    from .project import Project
    from .project_member import ProjectMember
    from .upload import Upload


class User(Base):
    """Users table."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(60), nullable=False)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name: Mapped[str] = column_property(first_name + " " + last_name)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_email_confirmed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=utcnow(), nullable=False
    )

    api_key: Mapped["APIKey"] = relationship(
        back_populates="owner", cascade="all, delete"
    )
    campaigns: Mapped[list["Campaign"]] = relationship(
        back_populates="lead", cascade="all, delete"
    )
    flights: Mapped[list["Flight"]] = relationship(
        back_populates="pilot", cascade="all, delete"
    )
    project_memberships: Mapped[list["ProjectMember"]] = relationship(
        back_populates="member"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", cascade="all, delete"
    )
    team_memberships: Mapped[list["TeamMember"]] = relationship(back_populates="member")
    teams: Mapped[list["Team"]] = relationship(
        back_populates="owner", cascade="all, delete"
    )
    upload: Mapped[list["Upload"]] = relationship(
        back_populates="uploader", cascade="all, delete"
    )

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, email={self.email!r}, "
            f"first_name={self.first_name!r}, last_name={self.last_name!r}, "
            f"is_approved={self.is_approved!r}, "
            f"is_email_confirmed={self.is_email_confirmed!r}, "
            f"is_superuser={self.is_superuser!r}, created_at={self.created_at!r})"
        )
