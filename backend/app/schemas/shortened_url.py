from datetime import datetime
from typing import Optional

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, UUID4


# Shared properties
class ShortenedUrlBase(BaseModel):
    clicks: Optional[int] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    last_accessed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    original_url: Optional[str] = None
    short_id: Optional[str] = None


# Properties required on creation
class ShortenedUrlCreate(ShortenedUrlBase):
    original_url: str
    short_id: str
    user_id: UUID4
    expires_at: Optional[datetime] = None


# Properties required on update
class ShortenedUrlUpdate(ShortenedUrlBase):
    pass


# Properties in database
class ShortenedUrlInDBBase(ShortenedUrlBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    clicks: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    last_accessed_at: Optional[datetime] = None
    updated_at: datetime
    original_url: str
    short_id: str
    user_id: UUID4


# Properties returned by CRUD
class ShortenedUrl(ShortenedUrlInDBBase):
    pass


# Properties returned by API
class ShortenedUrlApiResponse(BaseModel):
    shortened_url: AnyHttpUrl


# Properties for URL payload
class UrlPayload(BaseModel):
    url: str
