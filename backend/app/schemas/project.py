from datetime import date, datetime
from typing import Dict, Literal, Optional

from geojson_pydantic import Feature, Polygon
from pydantic import BaseModel, Field, field_validator, ValidationInfo, UUID4

from app.schemas.location import LocationCreate


# shared properties
class ProjectBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    planting_date: Optional[date] = None
    harvest_date: Optional[date] = None
    # relationships
    location_id: Optional[UUID4] = None
    team_id: Optional[UUID4] = None

    @field_validator("harvest_date")
    @classmethod
    def end_date_after_or_on_start_date(
        cls, v: Optional[date], info: ValidationInfo
    ) -> Optional[date]:
        if (
            "planting_date" in info.data
            and v is not None
            and info.data["planting_date"] is not None
            and v < info.data["planting_date"]
        ):
            raise ValueError("harvest_date cannot be before planting_date")
        return v


# properties to save in DB on creation
class ProjectCreate(ProjectBase):
    title: str
    description: str
    location: LocationCreate  # GeoJSON Feature


# properties to receive via API on update
class ProjectUpdate(ProjectBase):
    pass


# properties shared by models stored in DB
class ProjectInDBBase(ProjectBase, from_attributes=True):
    title: str
    description: str
    # internal
    id: UUID4
    is_active: bool
    deactivated_at: Optional[datetime] = None
    owner_id: UUID4 = Field(exclude=True)
    # relationships
    location_id: UUID4


# additional properties to return via API
class Project(ProjectInDBBase):
    # properties created after queries
    field: Optional[Feature[Polygon, Dict]] = None
    flight_count: int = 0
    most_recent_flight: Optional[date] = None
    role: Literal["owner", "manager", "viewer"]


# project boundary centroid
class Centroid(BaseModel):
    x: float
    y: float


# schema returned when multiple projects requested
class Projects(BaseModel):
    id: UUID4
    centroid: Centroid
    description: str
    flight_count: int = 0
    most_recent_flight: Optional[date] = None
    role: Literal["owner", "manager", "viewer"]
    title: str


# additional properties stored in DB
class ProjectInDB(ProjectInDBBase):
    pass
