import uuid
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .project import Project
    from .flight import Flight
    from .data_product import DataProduct


class VectorLayer(Base):
    __tablename__ = "vector_layers"

    # columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    layer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    layer_id: Mapped[str] = mapped_column(String(12), nullable=False)
    geom: Mapped[str] = mapped_column(Geometry(), nullable=False)
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )
    flight_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("flights.id"), nullable=True
    )
    data_product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id"), nullable=True
    )
    # relationships
    project: Mapped["Project"] = relationship(back_populates="vector_layer")
    flight: Mapped["Flight"] = relationship(back_populates="vector_layer")
    data_product: Mapped["DataProduct"] = relationship(back_populates="vector_layer")

    def __repr__(self) -> str:
        return (
            f"VectorLayer(id={self.id!r}, layer_name={self.layer_name!r}), "
            f"layer_id={self.layer_id!r}, geom={self.geom!r}, "
            f"properties={self.properties!r}, is_active={self.is_active!r}, "
            f"project_id={self.project_id!r}, flight_id={self.flight_id!r}, "
            f"data_product_id={self.data_product_id!r})"
        )
