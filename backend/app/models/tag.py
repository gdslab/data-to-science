import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow

if TYPE_CHECKING:
    from .annotation_tag import AnnotationTag


class Tag(Base):
    __tablename__ = "tags"

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )

    # Relationships
    annotation_tags: Mapped[List["AnnotationTag"]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (Index("uq_tag_name_ci", func.lower(name), unique=True),)

    def __repr__(self) -> str:
        return (
            f"Tag(id={self.id!r}, name={self.name!r}, "
            f"created_at={self.created_at!r}, updated_at={self.updated_at!r})"
        )
