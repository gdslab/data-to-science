from datetime import datetime
from typing import Optional

from pydantic import BaseModel, UUID4


# Shared properties
class DiskUsageStatsBase(BaseModel):
    disk_free: Optional[int] = None
    disk_total: Optional[int] = None
    disk_used: Optional[int] = None
    recorded_at: Optional[datetime] = None


# Properties required on creation
class DiskUsageStatsCreate(DiskUsageStatsBase):
    disk_free: int
    disk_total: int
    disk_used: int


# Properties required on update
class DiskUsageStatsUpdate(DiskUsageStatsBase):
    disk_free: int
    disk_total: int
    disk_used: int
    recorded_at: datetime


# Properties in database
class DiskUsageStatsInDBBase(DiskUsageStatsBase):
    id: UUID4
    disk_free: int
    disk_total: int
    disk_used: int
    recorded_at: datetime


# Properties returned by CRUD
class DiskUsageStats(DiskUsageStatsInDBBase):
    pass
