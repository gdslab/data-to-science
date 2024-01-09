from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel

if TYPE_CHECKING:
    EmailStr = str
else:
    from pydantic import EmailStr


# shared properties
class TeamMemberBase(BaseModel):
    email: EmailStr | None


# properties to receive via API on creation
class TeamMemberCreate(TeamMemberBase):
    email: EmailStr


# properties to receive via API on update
class TeamMemberUpdate(TeamMemberBase):
    pass


# properties shared by models stored in DB
class TeamMemberInDBBase(TeamMemberBase, from_attributes=True):
    id: UUID
    member_id: UUID

    team_id: UUID


# additional properties to return via API
class TeamMember(TeamMemberInDBBase):
    full_name: str | None = None
    email: EmailStr | None = None
    profile_url: AnyHttpUrl | None = None


# additional properties stored in DB
class TeamMemberInDB(TeamMemberInDBBase):
    pass
