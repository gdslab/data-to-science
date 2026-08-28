from datetime import datetime
from typing import Optional

from pydantic import UUID4, BaseModel, Field


# shared properties
class AnnotationAttachmentBase(BaseModel):
    original_filename: Optional[str] = Field(default=None, min_length=1, max_length=255)
    filepath: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content_type: Optional[str] = Field(default=None, min_length=1, max_length=127)
    size_bytes: Optional[int] = Field(default=None, ge=0)
    width_px: Optional[int] = Field(default=None, ge=1)
    height_px: Optional[int] = Field(default=None, ge=1)
    duration_seconds: Optional[float] = Field(default=None, ge=0.0)


# properties to receive via API on creation
class AnnotationAttachmentCreate(AnnotationAttachmentBase):
    original_filename: str = Field(min_length=1, max_length=255)
    filepath: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=127)
    size_bytes: int = Field(ge=0)


# properties to receive via API on update
class AnnotationAttachmentUpdate(AnnotationAttachmentBase):
    pass


# properties shared by models stored in DB
class AnnotationAttachmentInDBBase(AnnotationAttachmentBase, from_attributes=True):
    id: UUID4
    original_filename: str
    filepath: str
    content_type: str
    size_bytes: int
    annotation_id: UUID4
    created_at: datetime
    updated_at: datetime


# additional properties to return via API
class AnnotationAttachment(AnnotationAttachmentInDBBase):
    pass


# additional properties stored in DB
class AnnotationAttachmentInDB(AnnotationAttachmentInDBBase):
    pass
