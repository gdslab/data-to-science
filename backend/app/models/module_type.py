import uuid
from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .project_module import ProjectModule


class ModuleType(Base):
    __tablename__ = "module_types"

    # Columns
    module_name: Mapped[str] = mapped_column(String(50), primary_key=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=True)

    # Relationships
    project_modules: Mapped[List["ProjectModule"]] = relationship(
        back_populates="module_type"
    )

    def __repr__(self) -> str:
        return (
            f"ModuleType(module_name={self.module_name!r}, "
            f"label={self.label!r}, description={self.description!r}, "
            f"sort_order={self.sort_order!r})"
        )
