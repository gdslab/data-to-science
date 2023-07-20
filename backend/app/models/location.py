import uuid
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from shapely.geometry import Polygon
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .project import Project


class Location(Base):
    __tablename__ = "locations"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    geom: Mapped[Polygon] = mapped_column(Geometry("POLYGON"), nullable=False)

    projects: Mapped[list["Project"]] = relationship(back_populates="location")
