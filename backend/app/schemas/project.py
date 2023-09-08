from datetime import date
from uuid import UUID

from pydantic import BaseModel
from app.schemas.location import PolygonGeoJSONFeature


# shared properties
class ProjectBase(BaseModel):
    title: str | None = None
    description: str | None = None
    planting_date: date | None = None
    harvest_date: date | None = None
    location_id: UUID | None = None
    team_id: UUID | None = None


# properties to receive via API on creation
class ProjectCreate(ProjectBase):
    title: str
    description: str
    planting_date: date
    harvest_date: date | None = None
    location_id: UUID
    team_id: UUID | None = None


# properties to receive via API on update
class ProjectUpdate(ProjectBase):
    pass


# properties shared by models stored in DB
class ProjectInDBBase(ProjectBase, from_attributes=True):
    id: UUID
    title: str
    description: str
    planting_date: date
    harvest_date: date | None = None

    location_id: UUID
    team_id: UUID | None = None
    owner_id: UUID


# additional properties to return via API
class Project(ProjectInDBBase):
    is_owner: bool = False
    field: PolygonGeoJSONFeature | None = None


# additional properties stored in DB
class ProjectInDB(ProjectInDBBase):
    pass
