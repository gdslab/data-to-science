import uuid
from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .project import Project
    from .user import User


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    form_data: Mapped[dict] = mapped_column(JSONB, nullable=True)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deactivated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    lead: Mapped["User"] = relationship(back_populates="campaigns")
    project: Mapped["Project"] = relationship(back_populates="campaigns")

    def __repr__(self) -> str:
        return (
            f"Campaign(id={self.id!r}, form_data={self.form_data!r}, "
            f"lead_id={self.lead_id!r}, project_id={self.project_id!r}, "
            f"is_active={self.is_active!r}, deactivated_at={self.deactivated_at!r})"
        )
