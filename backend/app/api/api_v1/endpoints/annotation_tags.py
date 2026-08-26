import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.schemas.annotation_tag import (
    AnnotationTag,
    AnnotationTagCreate,
)

router = APIRouter()

logger = logging.getLogger("__name__")


@router.post("", response_model=AnnotationTag, status_code=status.HTTP_201_CREATED)
def create_annotation_tag(
    annotation_tag_in: AnnotationTagCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create a new annotation tag."""
    annotation_tag = crud.annotation_tag.create(db, obj_in=annotation_tag_in)
    return annotation_tag
