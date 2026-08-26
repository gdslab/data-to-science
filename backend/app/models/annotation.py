import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from geoalchemy2 import Geometry
from geoalchemy2 import functions as geofunc
from sqlalchemy import DateTime, ForeignKey, Text, cast, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums.visibility import Visibility
from app.models.utils.utcnow import utcnow

if TYPE_CHECKING:
    from .annotation_attachment import AnnotationAttachment
    from .annotation_tag import AnnotationTag
    from .data_product import DataProduct
    from .user import User


class Annotation(Base):
    __tablename__ = "annotations"

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326), nullable=False
    )
    feature_geojson = column_property(
        func.jsonb_build_object(
            "type",
            "Feature",
            "geometry",
            cast(geofunc.ST_AsGeoJSON(geom), JSONB),
            "properties",
            func.jsonb_build_object(),
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )
    visibility: Mapped[Visibility] = mapped_column(
        ENUM(Visibility, name="visibility_scope"),
        nullable=False,
        default=Visibility.OWNER,
        server_default=Visibility.OWNER.value,
    )
    style: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Foreign keys
    data_product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    data_product: Mapped["DataProduct"] = relationship(
        back_populates="annotations",
        lazy="joined",
    )
    attachments: Mapped[List["AnnotationAttachment"]] = relationship(
        back_populates="annotation", cascade="all, delete-orphan", passive_deletes=True
    )
    created_by: Mapped[Optional["User"]] = relationship(back_populates="annotations")
    tag_rows: Mapped[List["AnnotationTag"]] = relationship(
        back_populates="annotation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"Annotation(id={self.id!r}, description={self.description!r}, "
            f"created_at={self.created_at!r}, updated_at={self.updated_at!r}, "
            f"data_product_id={self.data_product_id!r})"
        )
