import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base_class import Base
from app.models.utils.utcexpire import utcexpire
from app.models.utils.utcnow import utcnow

if TYPE_CHECKING:
    from .data_product import DataProduct
    from .raw_data import RawData


class FilePermission(Base):
    __tablename__ = "file_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcexpire(),
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=True
    )

    # NOTE: file_id references DataProduct. In a future update, this will be
    # renamed to data_product_id for clarity. For now, maintaining backward compatibility.
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id"), nullable=True
    )

    # NEW: Add raw_data_id for RawData file permissions
    raw_data_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("raw_data.id"), nullable=True
    )

    # Existing relationship (unchanged)
    file: Mapped["DataProduct"] = relationship(back_populates="file_permission")

    # NEW: Add raw_data relationship
    raw_data: Mapped["RawData"] = relationship(back_populates="file_permission")

    __table_args__ = (
        # Existing constraint (unchanged)
        UniqueConstraint("file_id", name="unique_to_file_permissions"),
        # NEW: Add unique constraint for raw_data_id
        UniqueConstraint("raw_data_id", name="unique_raw_data_id_file_permissions"),
        # NEW: Add check constraint to ensure at least one ID is present
        CheckConstraint(
            "(file_id IS NOT NULL) OR (raw_data_id IS NOT NULL)",
            name="check_at_least_one_file_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"FilePermission(id={self.id!r}, is_public={self.is_public!r}, "
            f"created_at={self.created_at!r}, expires_at={self.expires_at!r}, "
            f"last_accessed_at={self.last_accessed_at!r}, file_id={self.file_id!r}, "
            f"raw_data_id={self.raw_data_id!r})"
        )
