from typing import Optional

from pydantic import BaseModel, EmailStr


# shared properties
class GroupBase(BaseModel):
    name: str | None = None


# properties to receive via API on creation
class GroupCreate(GroupBase):
    name: str


# properties to receive via API on update
class GroupUpdate(GroupBase):
    name: str | None = None


class GroupInDBBase(GroupBase):
    # add database properties here that 
    # should be returned via API in Group
    name: str
    owner_id: int

    class Config:
        orm_mode = True


# additional properties to return via API
class Group(GroupInDBBase):
    pass


# additional properties stored in DB
class GroupInDB(GroupInDBBase):
    id: int
