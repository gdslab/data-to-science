from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import UUID4, BaseModel, Field, field_validator

if TYPE_CHECKING:
    from app.schemas.tag import Tag


# shared properties
class AnnotationTagBase(BaseModel):
    tag_id: Optional[UUID4] = None


# properties to receive via API on creation
class AnnotationTagCreate(BaseModel):
    tag: str = Field(min_length=1, max_length=255)

    @field_validator("tag")
    @classmethod
    def validate_tag(cls, v: str) -> str:
        """Normalize tag to lowercase and strip whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Tag cannot be empty or only whitespace")
        return v.lower()


# properties to receive via API on update
class AnnotationTagUpdate(AnnotationTagBase):
    pass


# properties shared by models stored in DB
class AnnotationTagInDBBase(AnnotationTagBase, from_attributes=True):
    id: UUID4
    annotation_id: UUID4
    tag_id: UUID4
    created_at: datetime
    updated_at: datetime


# additional properties to return via API
class AnnotationTag(AnnotationTagInDBBase):
    tag: Optional["Tag"] = None


# additional properties stored in DB
class AnnotationTagInDB(AnnotationTagInDBBase):
    pass
