from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .flight import Flight


DATA_TYPE_ENUM = ENUM("Ortho", "DSM", "PointCloud", "Other", name="data_product_type")


class DataProduct(Base):
    __tablename__ = "data_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_path: Mapped[str] = mapped_column(String, nullable=False)
    data_type: Mapped[enumerate] = mapped_column(DATA_TYPE_ENUM, nullable=False)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flights.id"), nullable=False)    

    flight: Mapped["Flight"] = relationship(back_populates="data_products")
