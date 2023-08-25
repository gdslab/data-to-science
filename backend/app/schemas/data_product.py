from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel


# shared properties
class DataProductBase(BaseModel):
    pass


# properties to receive via API on creation
class DataProductCreate(DataProductBase):
    filepath: str
    original_filename: str


# properties to receive via API on update
class DataProductUpdate(DataProductBase):
    pass


# properties shared by models stored in DB
class DataProductInDBBase(DataProductBase, from_attributes=True):
    id: UUID
    filepath: str
    flight_id: UUID
    original_filename: str


# additional properties to return via API
class DataProduct(DataProductInDBBase):
    status: str | None = None
    url: AnyHttpUrl


# additional properties stored in DB
class DataProductInDB(DataProductInDBBase):
    pass
