from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# base properties
class APIKeyBase(BaseModel):
    user_id: UUID | None = None


class APIKeyCreate(APIKeyBase):
    api_key: str
    user_id: UUID


class APIKeyUpdate(APIKeyBase):
    deactivated_at: datetime | None = None
    is_active: bool | None = None
    last_used_at: datetime | None = None
    total_requests: int | None = None


class APIKeyInDBBase(APIKeyBase):
    id: UUID
    api_key: str
    created_at: datetime
    is_active: bool
    last_used_at: datetime | None = None
    total_requests: int
    user_id: UUID
    deactivated_at: datetime | None = None


class APIKey(APIKeyInDBBase):
    pass
