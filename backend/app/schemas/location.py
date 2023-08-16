from uuid import UUID

from pydantic import BaseModel


class PolygonGeometry(BaseModel):
    type: str
    coordinates: list[list[tuple[float, float]]]


class PolygonGeoJSONFeature(BaseModel):
    type: str
    geometry: PolygonGeometry
    properties: dict[str, str]


# shared properties
class LocationBase(BaseModel):
    geom: str | None = None


# properties to receive via API on creation
class LocationCreate(LocationBase):
    geom: str


# properties to receive via API on update
class LocationUpdate(LocationBase):
    pass


# properties shared by models stored in DB
class LocationInDBBase(LocationBase):
    id: UUID
    geom: str

    class Config:
        orm_mode = True


# additional properties to return via API
class Location(LocationInDBBase):
    pass


# additional properties stored in DB
class LocationInDB(LocationInDBBase):
    pass
