from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.location import LocationCreate


def create_random_location(db: Session) -> models.Location:
    """Create random location."""
    location_in = LocationCreate(geom="SRID=4326;POLYGON((0 0,1 0,1 1,0 1,0 0))")
    return crud.location.create(db, obj_in=location_in)
