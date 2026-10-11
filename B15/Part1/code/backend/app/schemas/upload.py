from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# base properties
class UploadBase(BaseModel):
    upload_id: str | None = None
    is_uploading: bool | None = None
    user_id: str | None = None


class UploadCreate(UploadBase):
    upload_id: str
    is_uploading: bool
    user_id: UUID


class UploadUpdate(UploadBase):
    last_updated_at: datetime | None = None


class UploadInDBBase(UploadBase):
    id: UUID
    upload_id: str
    is_uploading: bool
    last_updated_at: datetime
    user_id: UUID


class Upload(UploadBase):
    pass
