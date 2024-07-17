import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .extension import Extension


class TeamExtension(Base):
    __tablename__ = "team_extensions"
    # columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    deactivated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # foreign keys
    extension_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extensions.id"), nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    # relationships
    extension: Mapped["Extension"] = relationship(back_populates="team_extensions")
    team: Mapped["Team"] = relationship(back_populates="extensions")
    # unique constraint
    __table_args__ = (
        UniqueConstraint(
            "extension_id", "team_id", name="unique_to_extension_and_team"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"TeamExtension(id={self.id!r}, deactivated_at={self.deactivated_at!r}, "
            f"is_active={self.is_active!r}, extension_id={self.extension_id!r}, "
            f"team_id={self.team_id!r})"
        )
