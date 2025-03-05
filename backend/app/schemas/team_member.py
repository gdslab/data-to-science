from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, EmailStr


class Role(Enum):
    OWNER = "owner"
    MEMBER = "member"


# shared properties
class TeamMemberBase(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[Role] = None


# properties to receive via API on creation
class TeamMemberCreate(TeamMemberBase):
    email: EmailStr


# properties to receive via API on update
class TeamMemberUpdate(TeamMemberBase):
    pass


# properties shared by models stored in DB
class TeamMemberInDBBase(TeamMemberBase, from_attributes=True):
    id: UUID
    role: Role

    member_id: UUID
    team_id: UUID


# additional properties to return via API
class TeamMember(TeamMemberInDBBase):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_url: Optional[AnyHttpUrl] = None
    role: Role


# additional properties stored in DB
class TeamMemberInDB(TeamMemberInDBBase):
    pass
