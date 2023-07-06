from uuid import UUID

from pydantic import BaseModel


# shared properties
class TeamMemberBase(BaseModel):
    role: str | None = None


# properties to receive via API on creation
class TeamMemberCreate(TeamMemberBase):
    role: str = "Standard"


# properties to receive via API on update
class TeamMemberUpdate(TeamMemberBase):
    pass


# properties shared by models stored in DB
class TeamMemberInDBBase(TeamMemberBase):
    id: UUID
    role: str

    member_id: UUID
    team_id: UUID

    class Config:
        orm_mode = True


# additional properties to return via API
class TeamMember(TeamMemberInDBBase):
    pass


# additional properties stored in DB
class TeamMemberInDB(TeamMemberInDBBase):
    pass
