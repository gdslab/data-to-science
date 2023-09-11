import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .flight import Flight
    from .job import Job


DATA_TYPES = ["dsm", "point_cloud", "ortho", "other"]


class DataProduct(Base):
    __tablename__ = "data_products"
    # columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    data_type: Mapped[enumerate] = mapped_column(
        ENUM(*DATA_TYPES, name="dtype"), nullable=False
    )
    filepath: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    # foreign keys
    flight_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("flights.id"), nullable=False
    )
    # relationships
    flight: Mapped["Flight"] = relationship(back_populates="data_products")
    jobs: Mapped[list["Job"]] = relationship(back_populates="data_product")

    def __repr__(self) -> str:
        return (
            f"DataProduct(id={self.id!r}, data_type={self.data_type!r}, "
            f"filepath={self.filepath!r}, original_filename={self.original_filename}, "
            f"flight_id={self.flight_id!r})"
        )
