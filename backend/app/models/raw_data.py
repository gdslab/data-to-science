import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow

if TYPE_CHECKING:
    from .flight import Flight
    from .job import Job
    from .file_permission import FilePermission


class RawData(Base):
    __tablename__ = "raw_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filepath: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    flight_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("flights.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_initial_processing_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
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

    flight: Mapped["Flight"] = relationship(back_populates="raw_data")
    jobs: Mapped[List["Job"]] = relationship(
        back_populates="raw_data", cascade="all, delete"
    )
    file_permission: Mapped["FilePermission"] = relationship(
        back_populates="raw_data", cascade="all, delete"
    )

    def __repr__(self) -> str:
        return (
            f"RawData(id={self.id!r}, filepath={self.filepath!r}, "
            f"original_filename={self.original_filename}, flight_id={self.flight_id!r})"
        )
