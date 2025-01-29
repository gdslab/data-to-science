import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow


if TYPE_CHECKING:
    from .user import User


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    upload_id: Mapped[str] = mapped_column(String(32), nullable=False)
    is_uploading: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    uploader: Mapped["User"] = relationship(back_populates="upload")

    def __repr__(self) -> str:
        return (
            f"Upload(id={self.id!r}, upload_id={self.upload_id!r}, "
            f"is_uploading={self.is_uploading!r}, "
            f"last_updated_at={self.last_updated_at!r})"
        )
