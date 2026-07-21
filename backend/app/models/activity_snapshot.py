import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow


class ActivitySnapshot(Base):
    """Daily snapshot of platform-wide user activity counts.

    Recorded once per day by a Celery beat task. Because ``users.last_activity_at``
    only stores each user's most recent activity timestamp, point-in-time active
    counts cannot be reconstructed historically; persisting them daily here builds
    the time series needed for DAU/WAU/MAU trends and stickiness.
    """

    __tablename__ = "activity_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    snapshot_date: Mapped[date] = mapped_column(
        Date, unique=True, index=True, nullable=False
    )
    # Distinct users active within the trailing window at snapshot time.
    active_24h: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_7d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_30d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"ActivitySnapshot(id={self.id!r}, snapshot_date={self.snapshot_date!r}, "
            f"active_24h={self.active_24h!r}, active_7d={self.active_7d!r}, "
            f"active_30d={self.active_30d!r}, new_users={self.new_users!r}, "
            f"total_users={self.total_users!r})"
        )
