import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow


class ShortenedUrl(Base):
    __tablename__ = "shortened_urls"

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clicks: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=None, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=None, nullable=True
    )
    original_url: Mapped[str] = mapped_column(nullable=False)
    short_id: Mapped[str] = mapped_column(nullable=False, unique=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )
    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    def __repr__(self) -> str:
        return (
            f"ShortenedUrl(id={self.id!r}, clicks={self.clicks!r}, "
            f"created_at={self.created_at!r}, expires_at={self.expires_at!r}, "
            f"is_active={self.is_active!r}, last_accessed_at={self.last_accessed_at!r}, "
            f"original_url={self.original_url!r}, short_id={self.short_id!r}, "
            f"updated_at={self.updated_at!r}, user_id={self.user_id!r})"
        )
