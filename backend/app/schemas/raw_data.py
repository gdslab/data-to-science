from datetime import datetime
from typing import List, Literal, Optional

from pydantic import AnyHttpUrl, BaseModel, UUID4


# shared properties
class RawDataBase(BaseModel):
    filepath: Optional[str] = None
    original_filename: Optional[str] = None
    is_active: Optional[bool] = True
    is_initial_processing_completed: bool = False


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
    is_initial_processing_completed: bool
    deactivated_at: Optional[datetime] = None


# additional properties to return via API
class RawData(RawDataInDBBase):
    has_active_job: bool = False
    report: Optional[str] = None
    status: Optional[str] = None
    url: Optional[AnyHttpUrl] = None


# additional properties stored in DB
class RawDataInDB(RawDataInDBBase):
    pass


class Product(BaseModel):
    data_type: str
    filename: str
    storage_path: str


class Report(BaseModel):
    filename: str
    storage_path: str
    raw_data_id: UUID4


class Status(BaseModel):
    code: int
    message: str


class RawDataMetadata(BaseModel):
    token: str
    job_id: UUID4
    status: Status
    products: List[Product]
    report: Optional[Report]


class ImageProcessingQueryParams(BaseModel):
    alignQuality: Literal["low", "medium", "high"]
    buildDepthQuality: Literal["low", "medium", "high"]
    camera: Literal["single", "multi"]
    disclaimer: bool
    keyPoint: int
    tiePoint: int
