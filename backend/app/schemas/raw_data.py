from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel


# shared properties
class RawDataBase(BaseModel):
    pass


# properties to receive via API on creation
class RawDataCreate(RawDataBase):
    filepath: str
    original_filename: str


# properties to receive via API on update
class RawDataUpdate(RawDataBase):
    pass


# properties shared by models stored in DB
class RawDataInDBBase(RawDataBase):
    id: UUID
    filepath: str
    flight_id: UUID
    original_filename: str

    class Config:
        orm_mode = True


# additional properties to return via API
class RawData(RawDataInDBBase):
    status: str | None = None
    url: AnyHttpUrl


# additional properties stored in DB
class RawDataInDB(RawDataInDBBase):
    pass
