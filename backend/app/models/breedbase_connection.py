import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class BreedbaseConnection(Base):
    __tablename__ = "breedbase_connections"

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    study_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))

    def __repr__(self) -> str:
        return (
            f"BreedbaseConnection(id={self.id}, base_url={self.base_url}, "
            f"study_id={self.study_id}, project_id={self.project_id})"
        )
