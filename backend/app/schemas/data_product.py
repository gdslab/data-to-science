from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel

from app.utils.ImageProcessor import STACProperties


# shared properties
class DataProductBase(BaseModel):
    data_type: str | None = None
    filepath: str | None = None
    original_filename: str | None = None
    stac_properties: STACProperties | None = None
    is_active: bool = True


# properties to receive via API on creation
class DataProductCreate(DataProductBase):
    data_type: str
    filepath: str
    original_filename: str
    stac_properties: STACProperties | None = None


# properties to receive via API on update
class DataProductUpdate(DataProductBase):
    pass


# properties shared by models stored in DB
class DataProductInDBBase(DataProductBase, from_attributes=True):
    id: UUID
    data_type: str
    filepath: str
    flight_id: UUID
    original_filename: str
    stac_properties: STACProperties | None = None
    user_style: dict | None = None
    is_active: bool
    deactivated_at: datetime | None = None


# additional properties to return via API
class DataProduct(DataProductInDBBase):
    status: str | None = None
    url: AnyHttpUrl | None = None


# additional properties stored in DB
class DataProductInDB(DataProductInDBBase):
    pass
