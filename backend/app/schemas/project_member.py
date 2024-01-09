from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel

if TYPE_CHECKING:
    EmailStr = str
else:
    from pydantic import EmailStr


# shared properties
class ProjectMemberBase(BaseModel):
    email: EmailStr | None = None
    member_id: UUID | None = None
    role: str | None = None


# properties to receive via API on creation
class ProjectMemberCreate(ProjectMemberBase):
    role: str = "viewer"


# properties to receive via API on update
class ProjectMemberUpdate(ProjectMemberBase):
    pass


# properties shared by models stored in DB
class ProjectMemberInDBBase(ProjectMemberBase, from_attributes=True):
    id: UUID
    role: str
    member_id: UUID

    project_id: UUID


# additional properties to return via API
class ProjectMember(ProjectMemberInDBBase):
    full_name: str | None = None
    email: EmailStr | None = None
    profile_url: AnyHttpUrl | None = None


# additional properties stored in DB
class ProjectMemberInDB(ProjectMemberInDBBase):
    pass
