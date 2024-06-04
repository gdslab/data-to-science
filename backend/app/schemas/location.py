from typing import Dict
from uuid import UUID

from geojson_pydantic import Feature, Polygon
from pydantic import BaseModel


# shared properties
class LocationBase(BaseModel):
    geojson: Feature[Polygon, Dict] | None = None


# properties to receive via API on creation
class LocationCreate(Feature[Polygon, Dict]):
    pass


# properties to receive via API on update
class LocationUpdate(LocationCreate):
    pass


# properties shared by models stored in DB
class LocationInDBBase(LocationBase, from_attributes=True):
    id: UUID

    geojson: Feature[Polygon, Dict]


# additional properties to return via API
class Location(LocationInDBBase):
    center_x: float
    center_y: float


# additional properties stored in DB
class LocationInDB(LocationInDBBase):
    pass
