import uuid
from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import column_property, Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.user import utcnow


if TYPE_CHECKING:
    from .flight import Flight
    from .team import Team
    from .team_member import TeamMember
    from .project import Project
    from .project_member import ProjectMember


class User(Base):
    """Users table."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str] = column_property(first_name + " " + last_name)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_email_confirmed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=utcnow(), nullable=False
    )

    flights: Mapped[list["Flight"]] = relationship(
        back_populates="pilot", cascade="all, delete"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", cascade="all, delete"
    )
    teams: Mapped[list["Team"]] = relationship(
        back_populates="owner", cascade="all, delete"
    )
    team_memberships: Mapped[list["TeamMember"]] = relationship(back_populates="member")
    project_memberships: Mapped[list["ProjectMember"]] = relationship(
        back_populates="member"
    )

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, email={self.email!r}, "
            f"first_name={self.firstName!r}, last_name={self.last_name!r}, "
            f"is_approved={self.is_approved!r}, "
            f"is_email_confirmed={self.email_confirmed!r}, "
            f"is_superuser={self.is_superuser!r}, created_at={self.created_at!r})"
        )
