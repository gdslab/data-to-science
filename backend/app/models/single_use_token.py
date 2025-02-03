import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow


class SingleUseToken(Base):
    __tablename__ = "single_use_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    token: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    def __repr__(self) -> str:
        return (
            f"SingleUseToken(id={self.id!r}, created_at={self.created_at!r}, "
            f"token={self.token!r}, user_id={self.user_id!r})"
        )
