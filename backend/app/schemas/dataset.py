from uuid import UUID

from pydantic import BaseModel


# shared properties
class DatasetBase(BaseModel):
    category: str | None = None


# properties to receive via API on creation
class DatasetCreate(DatasetBase):
    category: str


# properties to receive via API on update
class DatasetUpdate(DatasetBase):
    pass


# properties shared by models stored in DB
class DatasetInDBBase(DatasetBase):
    id: UUID

    project_id: UUID | None = None

    class Config:
        orm_mode = True


# additional properties to return via API
class Dataset(DatasetInDBBase):
    pass


# additional properties stored in DB
class DatasetInDB(DatasetInDBBase):
    pass
