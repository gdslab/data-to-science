import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base_class import Base

if TYPE_CHECKING:
    from .data_product import DataProduct
    from .user import User


class DataProductLike(Base):
    __tablename__ = "data_product_likes"

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    data_product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id", ondelete="CASCADE")
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="data_product_likes")
    data_product: Mapped["DataProduct"] = relationship(back_populates="likes")

    # Ensure that a user can only like a data product once
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "data_product_id",
            name="like_unique_to_data_product_and_user",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"DataProductLike(id={self.id}, user_id={self.user_id}, "
            f"data_product_id={self.data_product_id})"
        )
