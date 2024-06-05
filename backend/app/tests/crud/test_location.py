import json
from typing import Dict

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from geojson_pydantic import Feature, Polygon
from sqlalchemy.orm import Session

from app import crud
from app.schemas.location import LocationUpdate
from app.tests.utils.location import create_location


def test_create_location(db: Session) -> None:
    location: Feature[Polygon, Dict] = create_location(db)
    assert location
    assert isinstance(location, Feature[Polygon, Dict])
    assert location.properties
    assert "id" in location.properties
    assert "center_x" in location.properties
    assert "center_y" in location.properties
    assert isinstance(location.properties["center_x"], float)
    assert isinstance(location.properties["center_y"], float)


def test_read_location(db: Session) -> None:
    location = create_location(db)
    location_id = location.properties["id"]
    location_in_db = crud.location.get_geojson_location(db, location_id=location_id)
    assert location_in_db
    assert isinstance(location_in_db, Feature[Polygon, Dict])
    assert location.properties["id"] == location_in_db.properties["id"]
    assert location.properties["center_x"] == location_in_db.properties["center_x"]
    assert location.properties["center_y"] == location_in_db.properties["center_y"]
    assert location.geometry == location_in_db.geometry


def test_update_location(db: Session) -> None:
    location = create_location(db)
    new_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [150.0, 50.0],
                    [151.0, 50.0],
                    [151.0, 51.0],
                    [150.0, 51.0],
                    [150.0, 50.0],
                ],
            ],
        },
        "properties": {
            "prop0": "value0",
            "prop1": {
                "this": "that",
            },
        },
    }
    location_in_update = LocationUpdate(**new_geojson)
    location_updated = crud.location.update_location(
        db,
        obj_in=location_in_update,
        location_id=location.properties["id"],
    )
    assert location_updated
    assert location.properties["id"] == location_updated.properties["id"]
    assert location.properties["center_x"] != location_updated.properties["center_x"]
    assert location.properties["center_y"] != location_updated.properties["center_y"]


def test_delete_location(db: Session) -> None:
    location = create_location(db)
    location_id = location.properties["id"]
    location_removed = crud.location.remove(db, id=location_id)
    location_get_after_removed = crud.location.get(db, id=location_id)
    assert location_get_after_removed is None
    assert location_removed
    assert str(location_removed.id) == location.properties["id"]
