from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from geojson_pydantic import Feature
from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator

from app.models.enums.visibility import Visibility

if TYPE_CHECKING:
    from app.schemas.annotation_attachment import AnnotationAttachment
    from app.schemas.annotation_tag import AnnotationTag
    from app.schemas.data_product import DataProduct
    from app.schemas.user import User


# shared properties
class AnnotationBase(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1)
    geom: Optional[Feature] = None


# properties to receive via API on creation
class AnnotationCreate(AnnotationBase):
    description: str = Field(min_length=1)
    geom: Feature
    tags: List[str] = Field(default_factory=list)
    visibility: Visibility = Visibility.OWNER
    style: Optional[dict] = None

    @field_validator("visibility", mode="before")
    @classmethod
    def normalize_visibility(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.upper()
        return v


# properties to receive via API on update
class AnnotationUpdate(AnnotationBase):
    tags: Optional[List[str]] = None
    visibility: Optional[Visibility] = None
    style: Optional[dict] = None

    @field_validator("visibility", mode="before")
    @classmethod
    def normalize_visibility(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.upper()
        return v


# properties shared by models stored in DB
class AnnotationInDBBase(AnnotationBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID4
    description: str
    # Map ORM attribute "feature_geojson" into response field "geom"
    geom: Feature = Field(validation_alias="feature_geojson")
    data_product_id: UUID4
    created_by_id: Optional[UUID4] = None
    visibility: Visibility = Visibility.OWNER
    style: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


# additional properties to return via API
class Annotation(AnnotationInDBBase):
    attachments: List["AnnotationAttachment"] = []
    created_by: Optional["User"] = None
    data_product: Optional["DataProduct"] = None
    tag_rows: List["AnnotationTag"] = []


# additional properties stored in DB
class AnnotationInDB(AnnotationInDBBase):
    pass
