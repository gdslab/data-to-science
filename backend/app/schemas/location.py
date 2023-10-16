from uuid import UUID

from pydantic import BaseModel


class PolygonGeometry(BaseModel):
    type: str
    coordinates: list[list[tuple[float, float]]]


class PolygonGeoJSONFeature(BaseModel):
    type: str
    geometry: PolygonGeometry
    properties: dict[str, str | float]


# shared properties
class LocationBase(BaseModel):
    center_x: float | None = None
    center_y: float | None = None
    geom: str | None = None


# properties to receive via API on creation
class LocationCreate(LocationBase):
    pass


# properties to receive via API on update
class LocationUpdate(LocationBase):
    pass


# properties shared by models stored in DB
class LocationInDBBase(LocationBase, from_attributes=True):
    id: UUID


# additional properties to return via API
class Location(LocationInDBBase):
    pass


# additional properties stored in DB
class LocationInDB(LocationInDBBase):
    pass
