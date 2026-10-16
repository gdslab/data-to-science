import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums.api_key_scope import APIKeyScope
from app.models.utils.utcnow import utcnow

if TYPE_CHECKING:
    from .user import User


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    api_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deactivated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scopes: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)), nullable=False, server_default=text("'{}'")
    )
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    owner: Mapped["User"] = relationship(back_populates="api_keys")

    def has_scope(self, scope: APIKeyScope) -> bool:
        return scope.value in (self.scopes or [])

    def __repr__(self) -> str:
        return (
            f"APIKey(id={self.id!r}, "
            f"created_at={self.created_at!r}, is_active={self.is_active!r}, "
            f"deactivated_at={self.deactivated_at!r}, "
            f"last_used_at={self.last_used_at!r}, name={self.name!r}, "
            f"scopes={self.scopes!r}, total_requests={self.total_requests!r}, "
            f"user_id={self.user_id!r})"
        )
