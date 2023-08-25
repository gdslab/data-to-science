import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .flight import Flight
    from .job import Job


class DataProduct(Base):
    __tablename__ = "data_product"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filepath: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    flight_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("flights.id"), nullable=False
    )

    flight: Mapped["Flight"] = relationship(back_populates="data_products")
    jobs: Mapped[list["Job"]] = relationship(back_populates="data_product")

    def __repr__(self) -> str:
        return (
            f"DataProduct(id={self.id!r}, filepath={self.filepath!r}, "
            f"original_filename={self.original_filename}, flight_id={self.flight_id!r})"
        )
