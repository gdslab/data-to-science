from datetime import date
from uuid import UUID

from pydantic import BaseModel


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
class ProjectInDBBase(ProjectBase):
    id: UUID
    title: str
    description: str
    planting_date: date
    harvest_date: date | None = None
    location_id: UUID
    team_id: UUID | None = None

    owner_id: UUID

    class Config:
        orm_mode = True


# additional properties to return via API
class Project(ProjectInDBBase):
    is_owner: bool = False


# additional properties stored in DB
class ProjectInDB(ProjectInDBBase):
    pass
