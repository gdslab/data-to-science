from typing import TypedDict

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.location import LocationCreate


TEST_COORDS = [
    [
        "-86.919558 40.420374",
        "-86.916082 40.420357",
        "-86.915932 40.424066",
        "-86.919107 40.424147",
        "-86.919537 40.423412",
        "-86.919558 40.420374",
    ],
    [
        "-84.919558 38.420374",
        "-84.916082 38.420357",
        "-84.915932 38.424066",
        "-84.919107 38.424147",
        "-84.919537 38.423412",
        "-84.919558 38.420374",
    ],
]
TEST_CENTROID = [
    {"lat": 40.42222989173847, "lon": -86.91776172873834},
    {"lat": 38.42222989173847, "lon": -84.91776172873834},
]


class SampleLocation(TypedDict):
    center_x: float
    center_y: float
    geom: str


SAMPLE_LOCATION: SampleLocation = {
    "center_x": TEST_CENTROID[0]["lon"],
    "center_y": TEST_CENTROID[0]["lat"],
    "geom": f"SRID=4326;POLYGON(({','.join(TEST_COORDS[0])}))",
}


def create_location(db: Session) -> models.Location:
    """Create random location."""

    location_in = LocationCreate(
        center_x=TEST_CENTROID[0]["lon"],
        center_y=TEST_CENTROID[0]["lat"],
        geom=f"SRID=4326;POLYGON(({','.join(TEST_COORDS[0])}))",
    )
    return crud.location.create(db, obj_in=location_in)
