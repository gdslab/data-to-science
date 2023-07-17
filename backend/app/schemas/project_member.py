from uuid import UUID

from pydantic import BaseModel


# shared properties
class ProjectMemberBase(BaseModel):
    role: str | None = None


# properties to receive via API on creation
class ProjectMemberCreate(ProjectMemberBase):
    role: str = "Standard"


# properties to receive via API on update
class ProjectMemberUpdate(ProjectMemberBase):
    pass


# properties shared by models stored in DB
class ProjectMemberInDBBase(ProjectMemberBase):
    id: UUID
    role: str

    member_id: UUID
    project_id: UUID

    class Config:
        orm_mode = True


# additional properties to return via API
class ProjectMember(ProjectMemberInDBBase):
    pass


# additional properties stored in DB
class ProjectMemberInDB(ProjectMemberInDBBase):
    pass
