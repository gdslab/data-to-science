import uuid
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry  # type: ignore
from sqlalchemy import Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .project import Project


class Location(Base):
    __tablename__ = "locations"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    center_x: Mapped[float] = mapped_column(Float, nullable=False)
    center_y: Mapped[float] = mapped_column(Float, nullable=False)
    geom: Mapped[str] = mapped_column(Geometry("POLYGON"), nullable=False)

    project: Mapped[list["Project"]] = relationship(back_populates="location")

    def __repr__(self) -> str:
        return (
            f"Location(id={self.id!r}, center_x={self.center_x!r}, "
            f"center_y={self.center_y!r}, geom={self.geom!r})"
        )
