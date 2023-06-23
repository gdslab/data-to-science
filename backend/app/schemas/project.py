from datetime import datetime

from pydantic import BaseModel


# shared properties
class ProjectBase(BaseModel):
    title: str | None = None
    description: str | None = None
    location: dict | None = None
    planting_date: datetime | None = None
    harvest_date: datetime | None = None


# properties to receive via API on creation
class ProjectCreate(ProjectBase):
    title: str
    location: dict


# properties to receive via API on update
class ProjectUpdate(ProjectBase):
    pass


# properties shared by models stored in DB
class ProjectInDBBase(ProjectBase):
    id: int
    title: str
    description: str
    location: dict
    planting_date: datetime
    harvest_date: datetime

    owner_id: int | None = None
    group_id: int | None = None

    class Config:
        orm_mode = True


# additional properties to return via API
class Project(ProjectInDBBase):
    pass


# additional properties stored in DB
class ProjectInDB(ProjectInDBBase):
    pass
