from datetime import datetime
from typing import Optional

from pydantic import BaseModel, UUID4


class JobBase(BaseModel):
    extra: Optional[dict] = None
    name: Optional[str] = None
    state: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data_product_id: Optional[UUID4] = None
    raw_data_id: Optional[UUID4] = None


class JobCreate(JobBase):
    extra: Optional[dict] = None
    name: str
    state: str
    status: str
    start_time: datetime
    data_product_id: Optional[UUID4] = None
    raw_data_id: Optional[UUID4] = None


class JobUpdate(JobBase):
    pass


class JobInDBBase(JobBase, from_attributes=True):
    id: UUID4
    extra: Optional[dict] = None
    name: str
    state: str
    status: str
    start_time: datetime
    data_product_id: Optional[UUID4] = None
    raw_data_id: Optional[UUID4] = None


class Job(JobInDBBase):
    pass


class JobInDB(JobInDBBase):
    pass
