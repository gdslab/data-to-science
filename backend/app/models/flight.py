import uuid
from typing import TYPE_CHECKING

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .data_product import DataProduct
    from .project import Project
    from .raw_data import RawData
    from .user import User

PLATFORMS = ["Phantom_4", "M300", "M350", "Other"]
SENSORS = ["RGB", "Multispectral", "LiDAR", "Other"]


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    acquisition_date: Mapped[date] = mapped_column(Date, nullable=False)
    altitude: Mapped[float] = mapped_column(Float, nullable=False)
    side_overlap: Mapped[float] = mapped_column(Float, nullable=False)
    forward_overlap: Mapped[float] = mapped_column(Float, nullable=False)
    sensor: Mapped[enumerate] = mapped_column(
        ENUM(*SENSORS, name="sensor_type"), nullable=False
    )
    platform: Mapped[enumerate] = mapped_column(
        ENUM(*PLATFORMS, name="platform_type"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deactivated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
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

    def __repr__(self) -> str:
        return (
            f"Flight(id={self.id!r}, acquisition_date={self.acquisition_date!r}, "
            f"altitude={self.altitude!r}, side_overlap={self.side_overlap!r}, "
            f"forward_overlap={self.forward_overlap!r}, "
            f"sensor={self.sensor!r}, platform={self.platform!r}, "
            f"is_active={self.is_active!r}, deactivated_at={self.deactivated_at!r}, "
            f"project_id={self.project_id!r}, pilot_id={self.pilot_id!r})"
        )
