import json
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post(
    "",
    response_model=schemas.location.PolygonGeoJSONFeature,
    status_code=status.HTTP_201_CREATED,
)
def create_location(
    location_in: schemas.LocationCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new location."""
    location = crud.location.create_with_owner(db, obj_in=location_in)
    geojson_location = crud.location.get_geojson_location(db, location_id=location.id)
    return json.loads(geojson_location)
