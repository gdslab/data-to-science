import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow

if TYPE_CHECKING:
    from .data_product import DataProduct
    from .user import User


class DataProductView(Base):
    __tablename__ = "data_product_views"

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )

    # Foreign keys
    data_product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id"), nullable=False
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    data_product: Mapped["DataProduct"] = relationship(back_populates="views")
    user: Mapped[Optional["User"]] = relationship(back_populates="data_product_views")

    __table_args__ = (
        CheckConstraint(
            "user_id IS NOT NULL OR session_id IS NOT NULL",
            name="dp_view_requires_viewer_identity",
        ),
        Index(
            "ix_dp_views_dp_id_user_id_viewed_at",
            "data_product_id",
            "user_id",
            "viewed_at",
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        Index(
            "ix_dp_views_dp_id_session_id_viewed_at",
            "data_product_id",
            "session_id",
            "viewed_at",
            postgresql_where=text("session_id IS NOT NULL"),
        ),
        Index(
            "ix_dp_views_data_product_id",
            "data_product_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"DataProductView(id={self.id}, data_product_id={self.data_product_id}, "
            f"user_id={self.user_id}, session_id={self.session_id}, "
            f"viewed_at={self.viewed_at})"
        )
