from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .group import Group
    from .user import User


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(300))
    location: Mapped[dict] = mapped_column(JSONB, nullable=False)
    planting_date: Mapped[datetime] = mapped_column(DateTime)
    harvest_date: Mapped[datetime] = mapped_column(DateTime)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))

    owner: Mapped["User"] = relationship(back_populates="projects")
    group: Mapped["Group"] = relationship(back_populates="projects")
