import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow

if TYPE_CHECKING:
    from .annotation import Annotation


class AnnotationAttachment(Base):
    __tablename__ = "annotation_attachments"

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(127), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Optional media attributes columns
    width_px: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height_px: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )

    # Foreign keys
    annotation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("annotations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    annotation: Mapped["Annotation"] = relationship(back_populates="attachments")

    # Constraints
    __table_args__ = (CheckConstraint("size_bytes >= 0", name="check_size_bytes"),)

    def __repr__(self) -> str:
        return (
            f"AnnotationAttachment(id={self.id!r}, original_filename={self.original_filename!r}, "
            f"filepath={self.filepath!r}, content_type={self.content_type!r}, "
            f"size_bytes={self.size_bytes!r}, "
            f"width_px={self.width_px!r}, height_px={self.height_px!r}, "
            f"duration_seconds={self.duration_seconds!r}, created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r}, annotation_id={self.annotation_id!r})"
        )
