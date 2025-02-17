import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow


class DiskUsageStats(Base):
    __tablename__ = "disk_usage_stats"

    # columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    disk_free: Mapped[int] = mapped_column(BigInteger, nullable=False)
    disk_total: Mapped[int] = mapped_column(BigInteger, nullable=False)
    disk_used: Mapped[int] = mapped_column(BigInteger, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"DiskUsageStats(id={self.id!r}, disk_free={self.disk_free!r}, "
            f"disk_used={self.disk_used!r}, disk_total={self.disk_total!r}, "
            f"recorded_at={self.recorded_at!r}) "
        )
