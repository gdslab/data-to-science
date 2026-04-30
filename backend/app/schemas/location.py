from typing import Any, Dict
from uuid import UUID

from geojson_pydantic import Feature, Polygon
from pydantic import BaseModel, field_validator


# shared properties
class LocationBase(BaseModel):
    geojson: Feature[Polygon, Dict] | None = None


# properties to receive via API on creation
class LocationCreate(Feature[Polygon, Dict]):
    @field_validator("geometry", mode="before")
    @classmethod
    def geometry_must_be_polygon(cls, v: Any) -> Any:
        # Short-circuit Pydantic's union resolution against Feature[Polygon, Dict]
        # so non-Polygon geometries return one clear domain message instead of
        # an 11-item Position2D/Position3D coordinate-coercion dump.
        geom_type = (
            v.get("type") if isinstance(v, dict) else getattr(v, "type", None)
        )
        if geom_type is None or geom_type == "Polygon":
            return v
        if geom_type == "MultiPolygon":
            raise ValueError(
                "Field boundary must be a single Polygon. MultiPolygon is not "
                "supported — dissolve the feature into a single Polygon before "
                "uploading."
            )
        raise ValueError(
            f"Field boundary must be a Polygon. Received geometry type: "
            f"{geom_type}."
        )


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
