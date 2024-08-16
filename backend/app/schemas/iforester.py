from datetime import datetime
from typing import Optional

from pydantic import BaseModel, UUID4


# properties in POST requests
class IForesterPost(BaseModel):
    DBH: Optional[float] = None
    depthFile: Optional[str] = None
    depthImageFileName: Optional[str] = None
    distance: Optional[float] = None
    image: Optional[str] = None
    imageFile: Optional[str] = None
    jsonPost: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    note: Optional[str] = None
    phoneDirection: Optional[float] = None
    phoneID: Optional[str] = None
    png: Optional[str] = None
    RGB1XImageFileName: Optional[str] = None
    species: Optional[str] = None
    user: Optional[str] = None


# shared properties stored in db
class IForesterBase(BaseModel):
    dbh: Optional[float] = None
    depthFile: Optional[str] = None
    distance: Optional[float] = None
    imageFile: Optional[str] = None
    jsonPost: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    note: Optional[str] = None
    phoneDirection: Optional[float] = None
    phoneID: Optional[str] = None
    species: Optional[str] = None
    user: Optional[str] = None


# properties to receive via API on creation
class IForesterCreate(IForesterBase):
    pass


# properties to receive via API on update
class IForesterUpdate(IForesterBase):
    pass


# properties shared by models stored in DB
class IForesterInDBBase(IForesterBase):
    id: UUID4
    timeStamp: datetime
    project_id: UUID4


# additional properties to return via API
class IForester(IForesterInDBBase):
    pass


# additional properties stored in DB
class IForesterInDB(IForesterInDBBase):
    pass
