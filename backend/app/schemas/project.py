from datetime import date, datetime
from typing import Dict
from uuid import UUID

from geojson_pydantic import Feature, Polygon
from pydantic import BaseModel
from app.schemas.location import LocationCreate


# shared properties
class ProjectBase(BaseModel):
    title: str | None = None
    description: str | None = None
    planting_date: date | None = None
    harvest_date: date | None = None
    is_active: bool = True
    location_id: UUID | None = None
    team_id: UUID | None = None


# properties to save in DB on creation
class ProjectCreate(ProjectBase):
    title: str
    description: str
    planting_date: date | None = None
    harvest_date: date | None = None
    location: LocationCreate
    location_id: UUID | None = None
    team_id: UUID | None = None


# properties to receive via API on update
class ProjectUpdate(ProjectBase):
    pass


# properties shared by models stored in DB
class ProjectInDBBase(ProjectBase, from_attributes=True):
    id: UUID
    title: str
    description: str
    planting_date: date | None = None
    harvest_date: date | None = None
    is_active: bool
    deactivated_at: datetime | None = None

    location_id: UUID
    team_id: UUID | None = None
    owner_id: UUID


# additional properties to return via API
class Project(ProjectInDBBase):
    is_owner: bool = False
    field: Feature[Polygon, Dict] | None = None
    flight_count: int = 0
    most_recent_flight: date | None = None


# additional properties stored in DB
class ProjectInDB(ProjectInDBBase):
    pass
