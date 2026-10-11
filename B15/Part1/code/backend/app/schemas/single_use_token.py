from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# shared properties
class SingleUseTokenBase(BaseModel):
    token: str | None = None


# properties to receive via API on creation
class SingleUseTokenCreate(SingleUseTokenBase):
    token: str


# properties to receive via API on update
class SingleUseTokenUpdate(SingleUseTokenBase):
    created_at: datetime | None


# properties shared by models stored in DB
class SingleUseTokenInDBBase(SingleUseTokenBase, from_attributes=True):
    id: UUID
    created_at: datetime
    token: str
    user_id: UUID


# additional properties to return via API
class SingleUseToken(SingleUseTokenInDBBase):
    pass


# additional properties stored in DB
class SingleUseTokenInDB(SingleUseTokenInDBBase):
    pass
