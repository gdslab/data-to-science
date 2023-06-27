import uuid
from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.user import utcnow


if TYPE_CHECKING:
    from .flight import Flight
    from .group import Group
    from .project import Project


class User(Base):
    """Users table."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=utcnow(), nullable=False)

    flights: Mapped[list["Flight"]] = relationship(
        back_populates="pilot", cascade="all, delete"
    )
    groups: Mapped[list["Group"]] = relationship(
        back_populates="owner", cascade="all, delete"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", cascade="all, delete"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r}, first_name={self.first_name!r}, last_name={self.last_name!r}, is_approved={self.is_approved!r}, is_superuser={self.is_superuser!r}, created_at={self.created_at!r})"
