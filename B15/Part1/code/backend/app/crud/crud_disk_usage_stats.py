from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.disk_usage_stats import DiskUsageStats
from app.schemas.disk_usage_stats import DiskUsageStatsCreate, DiskUsageStatsUpdate


class CRUDDiskUsageStats(
    CRUDBase[DiskUsageStats, DiskUsageStatsCreate, DiskUsageStatsUpdate]
):
    def get_latest(self, db: Session) -> Optional[DiskUsageStats]:
        """Returns the record with the most recent `recorded_at` datetime.

        Args:
            db (Session): Database session.

        Returns:
            Optional[DiskUsageStats]: Latest disk usage stats or None.
        """
        statement = (
            select(DiskUsageStats).order_by(DiskUsageStats.recorded_at.desc()).limit(1)
        )

        with db as session:
            result = session.scalar(statement)

            return result


disk_usage_stats = CRUDDiskUsageStats(DiskUsageStats)
