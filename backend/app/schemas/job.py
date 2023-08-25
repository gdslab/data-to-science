from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobBase(BaseModel):
    name: str | None = None
    state: str | None = None
    status: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    raw_data_id: UUID | None = None


class JobCreate(JobBase):
    name: str
    state: str
    status: str
    start_time: datetime
    raw_data_id: UUID | None = None


class JobUpdate(JobBase):
    pass


class JobInDBBase(JobBase, from_attributes=True):
    id: UUID
    name: str
    state: str
    status: str
    start_time: datetime
    raw_data_id: UUID | None = None


class Job(JobInDBBase):
    pass


class JobInDB(JobInDBBase):
    pass
