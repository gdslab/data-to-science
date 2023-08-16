from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post("/", response_model=schemas.Location, status_code=status.HTTP_201_CREATED)
def create_location(
    location_in: schemas.LocationCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new location."""
    location = crud.location.create_with_owner(db, obj_in=location_in)
    return location
