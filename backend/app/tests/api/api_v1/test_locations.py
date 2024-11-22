import os
from typing import Dict

from fastapi import status
from fastapi.testclient import TestClient
from geojson_pydantic import Feature, Polygon
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.location import create_location
from app.tests.utils.project import create_project
from app.tests.utils.utils import get_geojson_feature_collection


def test_read_location(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    # get feature used when initially creating project
    location_id = project.location_id
    location = crud.location.get_geojson_location(db, location_id=location_id)
    response = client.get(f"{settings.API_V1_STR}/locations/{project.id}/{location_id}")
    assert response.status_code == status.HTTP_200_OK
    location_from_db = response.json()
    assert Feature[Polygon, Dict](**location_from_db)
    location_from_db["properties"]["id"] == location_id
    location_from_db["properties"]["center_x"] == location.properties["center_x"]
    location_from_db["properties"]["center_y"] == location.properties["center_y"]
    location_from_db["geometry"] == location.geometry


def test_update_location(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    # get feature used when initially creating project
    location_id = project.location_id
    location = crud.location.get_geojson_location(db, location_id=location_id)
    update_data = {
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
    response = client.put(
        f"{settings.API_V1_STR}/locations/{project.id}/{location_id}",
        json=update_data,
    )
    assert response.status_code == status.HTTP_200_OK
    location_updated = response.json()
    assert Feature[Polygon, Dict](**location_updated)
    assert location_updated["properties"]["center_x"] != location.properties["center_x"]
    assert location_updated["properties"]["center_y"] != location.properties["center_y"]


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


# def test_upload_shapefile_zip_for_project_boundary_with_too_many_features(
#     client: TestClient, db: Session, normal_user_access_token: str
# ) -> None:
#     """Verify uploaded shapefile zip with missing parts is handled."""
#     shp_zip = os.path.join(
#         os.sep, "app", "app", "tests", "data", "too_many_features.zip"
#     )
#     with open(shp_zip, "rb") as data:
#         files = {"files": data}
#         r = client.post(
#             f"{settings.API_V1_STR}/locations/upload_project_boundary", files=files
#         )
#         assert r.status_code == 400


# def test_upload_shapefile_zip_for_map_layer_with_too_many_features(
#     client: TestClient, db: Session, normal_user_access_token: str
# ) -> None:
#     """Verify uploaded shapefile zip with missing parts is handled."""
#     shp_zip = os.path.join(
#         os.sep, "app", "app", "tests", "data", "too_many_features.zip"
#     )
#     with open(shp_zip, "rb") as data:
#         files = {"files": data}
#         r = client.post(
#             f"{settings.API_V1_STR}/locations/upload_vector_layer", files=files
#         )
#         assert r.status_code == 400
