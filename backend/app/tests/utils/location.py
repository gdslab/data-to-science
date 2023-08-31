from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.location import LocationCreate


def create_random_location(db: Session) -> models.Location:
    """Create random location."""
    coords = [
        "-86.919558 40.420374",
        "-86.916082 40.420357",
        "-86.915932 40.424066",
        "-86.919107 40.424147",
        "-86.919537 40.423412",
        "-86.919558 40.420374",
    ]
    location_in = LocationCreate(
        center_x=-86.91776172873834,
        center_y=40.42222989173847,
        geom=f"SRID=4326;POLYGON(({','.join(coords)}))",
    )
    return crud.location.create(db, obj_in=location_in)
