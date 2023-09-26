from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel


# shared properties
class DataProductBase(BaseModel):
    band_info: dict | None = None
    data_type: str | None = None
    filepath: str | None = None
    original_filename: str | None = None


# properties to receive via API on creation
class DataProductCreate(DataProductBase):
    band_info: dict | None = None
    data_type: str
    filepath: str
    original_filename: str


# properties to receive via API on update
class DataProductUpdate(DataProductBase):
    pass


# properties shared by models stored in DB
class DataProductInDBBase(DataProductBase, from_attributes=True):
    id: UUID
    band_info: dict | None = None
    data_type: str
    filepath: str
    flight_id: UUID
    original_filename: str
    user_style: dict | None = None


# additional properties to return via API
class DataProduct(DataProductInDBBase):
    status: str | None = None
    url: AnyHttpUrl | None = None


# additional properties stored in DB
class DataProductInDB(DataProductInDBBase):
    pass
