from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# shared properties
class RefreshTokenBase(BaseModel):
    user_id: UUID | None = None


# properties to receive via API on creation
class RefreshTokenCreate(RefreshTokenBase):
    jti: UUID
    user_id: UUID
    issued_at: datetime
    expires_at: datetime


# properties to receive via API on update
class RefreshTokenUpdate(BaseModel):
    revoked: bool | None = None


# properties shared by models stored in DB
class RefreshTokenInDBBase(RefreshTokenBase):
    model_config = ConfigDict(from_attributes=True)
    jti: UUID
    issued_at: datetime
    expires_at: datetime
    user_id: UUID
    revoked: bool


# additional properties to return via API
class RefreshToken(RefreshTokenInDBBase):
    pass


# additional properties stored in DB (if needed)
class RefreshTokenInDB(RefreshTokenInDBBase):
    pass
