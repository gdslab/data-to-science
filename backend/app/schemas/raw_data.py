from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel


# shared properties
class RawDataBase(BaseModel):
    filepath: str | None = None
    original_filename: str | None = None
    is_active: bool = True


# properties to receive via API on creation
class RawDataCreate(RawDataBase):
    filepath: str
    original_filename: str


# properties to receive via API on update
class RawDataUpdate(RawDataBase):
    pass


# properties shared by models stored in DB
class RawDataInDBBase(RawDataBase, from_attributes=True):
    id: UUID
    filepath: str
    flight_id: UUID
    original_filename: str
    is_active: bool
    deactivated_at: datetime | None = None


# additional properties to return via API
class RawData(RawDataInDBBase):
    status: str | None = None
    url: AnyHttpUrl | None = None


# additional properties stored in DB
class RawDataInDB(RawDataInDBBase):
    pass
