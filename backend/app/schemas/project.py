from datetime import date
from typing import TypedDict
from uuid import UUID

from pydantic import BaseModel


class Geometry(TypedDict):
    type: str
    coordinates: list[list[list[float]]]


class Feature(TypedDict):
    type: str
    geometry: Geometry
    properties: dict[str, str | int | float]


# shared properties
class ProjectBase(BaseModel):
    title: str | None = None
    description: str | None = None
    location: Feature | None = None
    planting_date: date | None = None
    harvest_date: date | None = None


# properties to receive via API on creation
class ProjectCreate(ProjectBase):
    title: str
    location: Feature


# properties to receive via API on update
class ProjectUpdate(ProjectBase):
    pass


# properties shared by models stored in DB
class ProjectInDBBase(ProjectBase):
    id: UUID
    title: str
    description: str
    location: Feature
    planting_date: date
    harvest_date: date

    owner_id: UUID | None = None
    group_id: UUID | None = None

    class Config:
        orm_mode = True


# additional properties to return via API
class Project(ProjectInDBBase):
    pass


# additional properties stored in DB
class ProjectInDB(ProjectInDBBase):
    pass
