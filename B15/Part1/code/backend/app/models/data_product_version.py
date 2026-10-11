"""DataProductVersion entity for tracking immutable dataset snapshots and lineage."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.data_product import DataProduct
    from app.models.user import User


class DataProductVersion(Base):
    """Represents an immutable snapshot of a scientific DataProduct over time.

    Implements the Memento / Temporal Object pattern to record dataset provenance,
    parameter revisions, and lineage history across photogrammetry re-runs.
    """

    __tablename__ = "data_product_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    data_product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[str] = mapped_column(String(32), nullable=False)
    commit_message: Mapped[str] = mapped_column(String(512), nullable=False)
    
    # Lineage tracking: parent version pointer forming a version DAG
    parent_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("data_product_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Point-in-time spatial and physical snapshot attributes
    filepath: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    stac_properties: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    bbox: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    crs: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    resolution: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Version status flags
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    data_product: Mapped["DataProduct"] = relationship(
        "DataProduct", backref="versions"
    )
    parent_version: Mapped[Optional["DataProductVersion"]] = relationship(
        "DataProductVersion", remote_side=[id], backref="child_versions"
    )
    created_by: Mapped[Optional["User"]] = relationship("User")
