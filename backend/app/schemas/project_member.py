from enum import Enum
from typing import Optional
from typing_extensions import Self
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, EmailStr, model_validator

from app.schemas.role import Role


# shared properties
class ProjectMemberBase(BaseModel):
    email: Optional[EmailStr] = None
    member_id: Optional[UUID] = None
    role: Optional[Role] = None


# properties to receive via API on creation
class ProjectMemberCreate(ProjectMemberBase):
    @model_validator(mode="after")
    def check_email_or_member_id(self) -> Self:
        if not self.email and not self.member_id:
            raise ValueError("Either email or member_id must be provided")
        return self


# properties to receive via API on update
class ProjectMemberUpdate(ProjectMemberBase):
    pass


# properties shared by models stored in DB
class ProjectMemberInDBBase(ProjectMemberBase, from_attributes=True):
    id: UUID
    role: Role

    member_id: UUID
    project_id: UUID


# additional properties to return via API
class ProjectMember(ProjectMemberInDBBase):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_url: Optional[AnyHttpUrl] = None
    role: Role


# additional properties stored in DB
class ProjectMemberInDB(ProjectMemberInDBBase):
    pass
