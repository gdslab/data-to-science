import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow

if TYPE_CHECKING:
    from .annotation import Annotation
    from .tag import Tag


class AnnotationTag(Base):
    __tablename__ = "annotation_tags"

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
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

    # Foreign keys
    annotation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("annotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    annotation: Mapped["Annotation"] = relationship(back_populates="tag_rows")
    tag: Mapped["Tag"] = relationship(back_populates="annotation_tags")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "annotation_id", "tag_id", name="uq_annotation_tag_annotation_id_tag_id"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"AnnotationTag(id={self.id!r}, "
            f"created_at={self.created_at!r}, updated_at={self.updated_at!r}, "
            f"annotation_id={self.annotation_id!r}, tag_id={self.tag_id!r})"
        )
