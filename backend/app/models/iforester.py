import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.user import utcnow


if TYPE_CHECKING:
    from .project import Project


class IForester(Base):
    __tablename__ = "iforester"

    # columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dbh: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    depthFile: Mapped[str] = mapped_column(String(255), nullable=True, default=None)
    distance: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    imageFile: Mapped[str] = mapped_column(String(255), nullable=True, default=None)
    jsonPost: Mapped[str] = mapped_column(String(1023), nullable=True, default=None)
    latitude: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    longitude: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    note: Mapped[str] = mapped_column(String(1023), nullable=True, default=None)
    phoneDirection: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    phoneID: Mapped[str] = mapped_column(String(63), nullable=True, default=None)
    species: Mapped[str] = mapped_column(String(31), nullable=True, default=None)
    timeStamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=utcnow(), nullable=False
    )
    user: Mapped[str] = mapped_column(String(31), nullable=True, default=None)
    # foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )
    # relationships
    project: Mapped["Project"] = relationship(back_populates="iforester")

    def __repr__(self) -> str:
        return (
            f"IForester(id={self.id!r}, dbh={self.dbh!r}, depthFile={self.depthFile!r}, "
            f"distance={self.distance!r}, imageFile={self.imageFile!r}, "
            f"jsonPost={self.jsonPost!r}, latitude={self.latitude!r}, "
            f"longitude={self.longitude!r}, note={self.note!r}, "
            f"phoneDirection={self.phoneDirection!r}, phoneId={self.phoneID!r}, "
            f"species={self.species!r}, timeStamp={self.timeStamp!r}, "
            f"user={self.user!r})"
        )
