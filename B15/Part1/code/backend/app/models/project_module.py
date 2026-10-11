import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .module_type import ModuleType
    from .project import Project


class ProjectModule(Base):
    __tablename__ = "project_modules"
    __table_args__ = (
        UniqueConstraint("project_id", "module_name", name="uq_project_module"),
    )

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Foreign keys
    module_name: Mapped[str] = mapped_column(
        String(50), ForeignKey("module_types.module_name"), primary_key=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), primary_key=True
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="modules")
    module_type: Mapped["ModuleType"] = relationship(back_populates="project_modules")

    def __repr__(self) -> str:
        return (
            f"ProjectModule(id={self.id!r}, module_name={self.module_name!r}, "
            f"project_id={self.project_id!r}, enabled={self.enabled!r})"
        )
