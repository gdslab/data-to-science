import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base_class import Base
from app.models.utils.utcexpire import utcexpire
from app.models.utils.utcnow import utcnow

if TYPE_CHECKING:
    from .data_product import DataProduct


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

    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id"), nullable=True
    )

    file: Mapped["DataProduct"] = relationship(back_populates="file_permission")

    __table_args__ = (UniqueConstraint("file_id", name="unique_to_file_permissions"),)

    def __repr__(self) -> str:
        return (
            f"FilePermission(id={self.id!r}, is_public={self.is_public!r}, "
            f"created_at={self.created_at!r}, expires_at={self.expires_at!r}, "
            f"last_accessed_at={self.last_accessed_at!r}, file_id={self.file_id!r})"
        )
