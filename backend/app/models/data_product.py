import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .flight import Flight


DATA_TYPE_ENUM = ENUM("Ortho", "DSM", "PointCloud", "Other", name="data_product_type")


class DataProduct(Base):
    __tablename__ = "data_products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_path: Mapped[str] = mapped_column(String, nullable=False)
    data_type: Mapped[enumerate] = mapped_column(DATA_TYPE_ENUM, nullable=False)
    flight_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("flights.id"), nullable=False)    

    flight: Mapped["Flight"] = relationship(back_populates="data_products")

    def __repr__(self) -> str:
        return f"DataProduct(id={self.id!r}, data_path={self.data_path!r}, data_type={self.data_type!r}, flight_id={self.flight_id!r})"
