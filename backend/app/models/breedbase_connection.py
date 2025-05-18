import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .project import Project


class BreedbaseConnection(Base):
    __tablename__ = "breedbase_connections"

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    trial_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))

    def __repr__(self) -> str:
        return (
            f"BreedbaseConnection(id={self.id}, base_url={self.base_url}, "
            f"trial_id={self.trial_id}, project_id={self.project_id})"
        )
