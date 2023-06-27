from uuid import UUID

from pydantic import BaseModel


# shared properties
class GroupBase(BaseModel):
    title: str | None = None
    description: str | None = None


# properties to receive via API on creation
class GroupCreate(GroupBase):
    title: str


# properties to receive via API on update
class GroupUpdate(GroupBase):
    pass


# properties shared by models stored in DB
class GroupInDBBase(GroupBase):
    id: UUID
    title: str

    owner_id: UUID

    class Config:
        orm_mode = True


# additional properties to return via API
class Group(GroupInDBBase):
    pass


# additional properties stored in DB
class GroupInDB(GroupInDBBase):
    pass
