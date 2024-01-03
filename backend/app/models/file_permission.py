import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.user import utcexpire, utcnow

ACCESS_TYPE = ["UNRESTRICTED", "RESTRICTED"]

if TYPE_CHECKING:
    from .data_product import DataProduct


class FilePermission(Base):
    __tablename__ = "file_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    access: Mapped[enumerate] = mapped_column(
        ENUM(*ACCESS_TYPE, name="access_type", nullable=False, default="RESTRICTED")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcexpire()
    )
    last_accessed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id"), nullable=True
    )

    file: Mapped["DataProduct"] = relationship(back_populates="file_permission")

    def __repr__(self) -> str:
        return (
            f"FilePermission(id={self.id!r}, name={self.access!r}, "
            f"created_at={self.created_at!r}, expires_at={self.expires_at!r}, "
            f"last_accessed_at={self.last_accessed_at!r}, file_id={self.file_id!r})"
        )
