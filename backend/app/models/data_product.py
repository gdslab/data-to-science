import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow

if TYPE_CHECKING:
    from .data_product_metadata import DataProductMetadata
    from .file_permission import FilePermission
    from .flight import Flight
    from .job import Job
    from .user_style import UserStyle
    from .vector_layer import VectorLayer


class DataProduct(Base):
    __tablename__ = "data_products"
    # columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    data_type: Mapped[str] = mapped_column(String(16), nullable=False)
    filepath: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    stac_properties: Mapped[dict] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_initial_processing_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
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
    # foreign keys
    flight_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("flights.id"), nullable=False
    )
    # relationships
    data_product_metadata: Mapped[List["DataProductMetadata"]] = relationship(
        back_populates="data_product", cascade="all, delete"
    )
    file_permission: Mapped["FilePermission"] = relationship(
        back_populates="file", cascade="all, delete"
    )
    flight: Mapped["Flight"] = relationship(back_populates="data_products")
    jobs: Mapped[List["Job"]] = relationship(
        back_populates="data_product", cascade="all, delete"
    )
    style: Mapped["UserStyle"] = relationship(
        back_populates="data_product", cascade="all, delete"
    )
    vector_layer: Mapped[List["VectorLayer"]] = relationship(
        back_populates="data_product", cascade="all, delete"
    )

    def __repr__(self) -> str:
        return (
            f"DataProduct(id={self.id!r}, data_type={self.data_type!r}, "
            f"filepath={self.filepath!r}, original_filename={self.original_filename}, "
            f"stac_properties={self.stac_properties!r}, is_active={self.is_active!r}, "
            f"deactivated_at={self.deactivated_at!r}, flight_id={self.flight_id!r})"
        )
