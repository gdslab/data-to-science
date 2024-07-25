import uuid
from typing import List, TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .team_extension import TeamExtension
    from .user_extension import UserExtension


class Extension(Base):
    __tablename__ = "extensions"
    # columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(String(128), nullable=True)
    # relationships
    team_extensions: Mapped[List["TeamExtension"]] = relationship(
        back_populates="extension", cascade="all, delete"
    )
    user_extensions: Mapped[List["UserExtension"]] = relationship(
        back_populates="extension", cascade="all, delete"
    )
    # unique constraint
    __table_args__ = (UniqueConstraint("name", name="unique_name"),)

    def __repr__(self) -> str:
        return (
            f"Extension(id={self.id!r}, name={self.name!r}, "
            f"description={self.description!r})"
        )
