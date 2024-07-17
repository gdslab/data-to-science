from typing import List, Optional, Union

from pydantic import BaseModel, UUID4


# shared properties
class TeamBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    new_members: Optional[List[UUID4]] = None
    project: Optional[Union[UUID4, str]] = None


# properties to receive via API on creation
class TeamCreate(TeamBase):
    title: str


# properties to receive via API on update
class TeamUpdate(TeamBase):
    pass


# properties shared by models stored in DB
class TeamInDBBase(TeamBase, from_attributes=True):
    id: UUID4
    title: str


# additional properties to return via API
class Team(TeamInDBBase):
    exts: List[str] = []
    is_owner: bool = False


# additional properties stored in DB
class TeamInDB(TeamInDBBase):
    owner_id: UUID4
