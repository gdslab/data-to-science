from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FilePermissionBase(BaseModel):
    is_public: bool | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
    last_accessed_at: datetime | None = None
    file_id: UUID | None = None


class FilePermissionCreate(FilePermissionBase):
    is_public: bool
    file_id: UUID


class FilePermissionUpdate(FilePermissionBase):
    pass


class FilePermissionInDBBase(FilePermissionBase):
    id: UUID
    is_public: bool
    created_at: datetime
    expires_at: datetime
    file_id: UUID


class FilePermission(FilePermissionInDBBase):
    pass


class FilePermissionInDB(FilePermissionInDBBase):
    pass
