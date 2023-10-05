from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# shared properties
class ConfirmationTokenBase(BaseModel):
    token: str | None = None


# properties to receive via API on creation
class ConfirmationTokenCreate(ConfirmationTokenBase):
    token: str


# properties to receive via API on update
class ConfirmationTokenUpdate(ConfirmationTokenBase):
    created_at: datetime | None


# properties shared by models stored in DB
class ConfirmationTokenInDBBase(ConfirmationTokenBase, from_attributes=True):
    id: UUID
    created_at: datetime
    token: str
    user_id: UUID


# additional properties to return via API
class ConfirmationToken(ConfirmationTokenInDBBase):
    pass


# additional properties stored in DB
class ConfirmationTokenInDB(ConfirmationTokenInDBBase):
    pass
