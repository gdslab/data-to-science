import os

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.location import create_location, TEST_CENTROID, TEST_COORDS
from app.tests.utils.project import create_project


def test_create_location(client: TestClient, normal_user_access_token: str) -> None:
    data = {
        "center_x": TEST_CENTROID[0]["lon"],
        "center_y": TEST_CENTROID[0]["lat"],
        "geom": f"SRID=4326;POLYGON(({','.join(TEST_COORDS[0])}))",
    }
    r = client.post(f"{settings.API_V1_STR}/locations", json=data)
    assert r.status_code == 201
    location_in_db = r.json()
    assert location_in_db["properties"]["center_x"] == data["center_x"]
    assert location_in_db["properties"]["center_y"] == data["center_y"]
    assert location_in_db["geometry"]["coordinates"] == [
        [
            [float(coord.split(" ")[0]), float(coord.split(" ")[1])]
            for coord in TEST_COORDS[0]
        ]
    ]


def test_update_location(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    location_id = project.location_id
    update_data = {
        "center_x": TEST_CENTROID[1]["lon"],
        "center_y": TEST_CENTROID[1]["lat"],
        "geom": f"SRID=4326;POLYGON(({','.join(TEST_COORDS[1])}))",
    }
    r = client.put(
        f"{settings.API_V1_STR}/locations/{project.id}/{location_id}", json=update_data
    )
    assert r.status_code == 200
    location_updated = r.json()
    assert location_updated["properties"]["center_x"] == update_data["center_x"]
    assert location_updated["properties"]["center_y"] == update_data["center_y"]
    assert location_updated["geometry"]["coordinates"] == [
        [
            [float(coord.split(" ")[0]), float(coord.split(" ")[1])]
            for coord in TEST_COORDS[1]
        ]
    ]


def test_upload_shapefile_zip(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify uploaded shapefile zip is unpacked, read, and returned as GeoJSON."""
    shp_zip = os.path.join(os.sep, "app", "app", "tests", "data", "single_field.zip")
    with open(shp_zip, "rb") as data:
        files = {"files": data}
        r = client.post(
            f"{settings.API_V1_STR}/locations/upload_project_boundary", files=files
        )
        assert r.status_code == 200
        fc = r.json()
        assert fc["type"] == "FeatureCollection"
        assert len(fc["features"]) > 0
        assert fc["features"][0]["geometry"]["type"] == "Polygon"


def test_upload_shapefile_zip_with_missing_parts(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify uploaded shapefile zip with missing parts is handled."""
    shp_zip = os.path.join(os.sep, "app", "app", "tests", "data", "incomplete-shp.zip")
    with open(shp_zip, "rb") as data:
        files = {"files": data}
        r = client.post(
            f"{settings.API_V1_STR}/locations/upload_project_boundary", files=files
        )
        assert r.status_code == 400
