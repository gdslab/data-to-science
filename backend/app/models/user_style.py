import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .data_product import DataProduct


class UserStyle(Base):
    __tablename__ = "user_styles"
    # columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # foreign keys
    data_product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    # relationships
    data_product: Mapped["DataProduct"] = relationship(back_populates="style")
    # unique constraint
    __table_args__ = (
        UniqueConstraint(
            "data_product_id", "user_id", name="unique_to_product_and_user"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"UserStyle(id={self.id!r}, settings={self.settings!r}, "
            f"data_product_id={self.data_product_id!r}, user_id={self.user_id!r})"
        )
