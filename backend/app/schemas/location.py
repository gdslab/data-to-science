from uuid import UUID

from pydantic import BaseModel


# shared properties
class LocationBase(BaseModel):
    name: str | None = None
    geom: str | None = None


# properties to receive via API on creation
class LocationCreate(LocationBase):
    name: str
    geom: str


# properties to receive via API on update
class LocationUpdate(LocationBase):
    pass


# properties shared by models stored in DB
class LocationInDBBase(LocationBase):
    id: UUID
    name: str
    geom: str

    class Config:
        orm_mode = True


# additional properties to return via API
class Location(LocationInDBBase):
    pass


# additional properties stored in DB
class LocationInDB(LocationInDBBase):
    pass
