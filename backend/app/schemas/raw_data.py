from uuid import UUID

from pydantic import BaseModel


# shared properties
class RawDataBase(BaseModel):
    pass


# properties to receive via API on creation
class RawDataCreate(RawDataBase):
    pass


# properties to receive via API on update
class RawDataUpdate(RawDataBase):
    pass


# properties shared by models stored in DB
class RawDataInDBBase(RawDataBase):
    id: UUID
    data_path: str
    flight_id: UUID

    class Config:
        orm_mode = True


# additional properties to return via API
class RawData(RawDataInDBBase):
    pass


# additional properties stored in DB
class RawDataInDB(RawDataInDBBase):
    pass
