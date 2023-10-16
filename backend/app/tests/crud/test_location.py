import json

from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app import crud
from app.schemas.location import LocationUpdate
from app.tests.utils.location import create_location, TEST_COORDS, TEST_CENTROID


def test_create_location(db: Session) -> None:
    location = create_location(db)
    assert location
    assert location.center_x == TEST_CENTROID[0].get("lon")
    assert location.center_y == TEST_CENTROID[0].get("lat")
    assert to_shape(location.geom).wkt == f"POLYGON (({', '.join(TEST_COORDS[0])}))"


def test_read_location(db: Session) -> None:
    location = create_location(db)
    location_in_db = crud.location.get(db, id=location.id)
    assert location_in_db
    assert location.id == location_in_db.id
    assert location.center_x == location_in_db.center_x
    assert location.center_y == location_in_db.center_y
    assert location.geom == location_in_db.geom


def test_update_location(db: Session) -> None:
    location = create_location(db)
    new_geom = f"SRID=4326;POLYGON(({','.join(TEST_COORDS[1])}))"
    new_center_x = TEST_CENTROID[1]["lat"]
    new_center_y = TEST_CENTROID[1]["lon"]
    location_in_update = LocationUpdate(
        center_x=new_center_x, center_y=new_center_y, geom=new_geom
    )
    location_updated = crud.location.update_location(
        db,
        obj_in=location_in_update,
        location_id=location.id,
    )
    assert location_updated
    location_geojson = json.loads(location_updated)
    assert str(location.id) == location_geojson["properties"]["id"]
    assert new_center_x == location_geojson["properties"]["center_x"]
    assert new_center_y == location_geojson["properties"]["center_y"]
    assert location_geojson["geometry"]["coordinates"] == [
        [
            [float(coord.split(" ")[0]), float(coord.split(" ")[1])]
            for coord in TEST_COORDS[1]
        ]
    ]


def test_delete_location(db: Session) -> None:
    location = create_location(db)
    location2 = crud.location.remove(db, id=location.id)
    location3 = crud.location.get(db, id=location.id)
    assert location3 is None
    assert location2
    assert location2.id == location.id
    assert location2.center_x == location.center_x
    assert location2.center_y == location.center_y
    assert location2.geom == location.geom
