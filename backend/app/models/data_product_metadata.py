import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .data_product import DataProduct


class DataProductMetadata(Base):
    __tablename__ = "data_product_metadata"

    # columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    properties: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # foreign keys (required)
    data_product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id"), nullable=False
    )

    # foreign keys (optional)
    vector_layer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vector_layers.id"), nullable=True
    )

    # relationships
    data_product: Mapped["DataProduct"] = relationship(
        back_populates="data_product_metadata"
    )
