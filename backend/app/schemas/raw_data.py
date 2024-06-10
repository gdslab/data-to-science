from datetime import datetime
from typing import List

from pydantic import AnyHttpUrl, BaseModel, UUID4


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
    id: UUID4
    filepath: str
    flight_id: UUID4
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


class Product(BaseModel):
    data_type: str
    filename: str
    storage_path: str


class RawDataMetadata(BaseModel):
    token: str
    products: List[Product]
