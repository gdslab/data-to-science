import uuid
from typing import TYPE_CHECKING

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow

if TYPE_CHECKING:
    from .data_product import DataProduct
    from .project import Project
    from .raw_data import RawData
    from .user import User
    from .vector_layer import VectorLayer

# default platforms, "Other" can be any string value
PLATFORMS = ["Phantom_4", "M300", "M350", "Other"]

# default sensors, only these exact values are accepted
SENSORS = ["RGB", "Multispectral", "LiDAR", "Thermal", "Hyperspectral", "Other"]


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    acquisition_date: Mapped[date] = mapped_column(Date, nullable=False)
    altitude: Mapped[float] = mapped_column(Float, nullable=False)
    side_overlap: Mapped[float] = mapped_column(Float, nullable=False)
    forward_overlap: Mapped[float] = mapped_column(Float, nullable=False)
    sensor: Mapped[enumerate] = mapped_column(
        ENUM(*SENSORS, name="sensor_type"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    read_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )
    pilot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    project: Mapped["Project"] = relationship(back_populates="flights")
    pilot: Mapped["User"] = relationship(back_populates="flights")

    data_products: Mapped[list["DataProduct"]] = relationship(
        back_populates="flight", cascade="all, delete", lazy="joined"
    )
    raw_data: Mapped[list["RawData"]] = relationship(
        back_populates="flight", cascade="all, delete", lazy="joined"
    )
    vector_layer: Mapped[list["VectorLayer"]] = relationship(back_populates="flight")

    def __repr__(self) -> str:
        return (
            f"Flight(id={self.id!r}, name={self.name!r}, "
            f"acquisition_date={self.acquisition_date!r}, "
            f"altitude={self.altitude!r}, side_overlap={self.side_overlap!r}, "
            f"forward_overlap={self.forward_overlap!r}, "
            f"sensor={self.sensor!r}, platform={self.platform!r}, "
            f"is_active={self.is_active!r}, deactivated_at={self.deactivated_at!r}, "
            f"project_id={self.project_id!r}, pilot_id={self.pilot_id!r})"
        )
