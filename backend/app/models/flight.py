from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .data_product import DataProduct
    from .project import Project
    from .raw_data import RawData
    from .user import User


PLATFORM_ENUM = ENUM("Phantom_4", "M300", "M350", "Other", name="platform_type")
SENSOR_ENUM = ENUM("RGB", "Multispectral", "LiDAR", "Other", name="sensor_type")


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(primary_key=True)
    acquisition_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    altitude: Mapped[float] = mapped_column(Float, nullable=False)
    side_overlap: Mapped[float] = mapped_column(Float, nullable=False)
    forward_overlap: Mapped[float] = mapped_column(Float, nullable=False)
    sensor: Mapped[enumerate] = mapped_column(SENSOR_ENUM, nullable=False)
    platform: Mapped[enumerate] = mapped_column(PLATFORM_ENUM, nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)    
    pilot_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    project: Mapped["Project"] = relationship(back_populates="flights")
    pilot: Mapped["User"] = relationship(back_populates="flights")
    data_products: Mapped[list["DataProduct"]] = relationship(
        back_populates="flight", cascade="all, delete"
    )
    raw_data: Mapped[list["RawData"]] = relationship(
        back_populates="flight", cascade="all, delete"
    )
