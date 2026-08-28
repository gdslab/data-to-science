from datetime import datetime
from typing import Optional

from pydantic import UUID4, BaseModel, Field


# shared properties
class TagBase(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)


# properties to receive via API on creation
class TagCreate(TagBase):
    name: str = Field(min_length=1, max_length=255)


# properties to receive via API on update
class TagUpdate(TagBase):
    pass


# properties shared by models stored in DB
class TagInDBBase(TagBase, from_attributes=True):
    id: UUID4
    name: str
    created_at: datetime
    updated_at: datetime


# additional properties to return via API
class Tag(TagInDBBase):
    pass


# additional properties stored in DB
class TagInDB(TagInDBBase):
    pass
