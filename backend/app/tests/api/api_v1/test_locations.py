import json
import os
from io import BytesIO
from typing import Dict

from fastapi import status
from fastapi.testclient import TestClient
from geojson_pydantic import Feature, Polygon
import pytest
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


def test_upload_geojson_with_invalid_coordinates(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify that GeoJSON with invalid geographic coordinates is rejected."""

    # Test with invalid longitude (outside -180 to 180 range)
    invalid_longitude_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [250.0, 40.0],  # Invalid longitude: 250 > 180
                            [251.0, 40.0],
                            [251.0, 41.0],
                            [250.0, 41.0],
                            [250.0, 40.0],
                        ],
                    ],
                },
                "properties": {"name": "test_polygon"},
            }
        ],
    }

    # Create a file-like object with the GeoJSON data
    geojson_file = BytesIO(json.dumps(invalid_longitude_geojson).encode())

    response = client.post(
        f"{settings.API_V1_STR}/locations/upload_project_boundary",
        files={"files": ("test.geojson", geojson_file, "application/json")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid longitude 250" in response.json()["detail"]
    assert "Must be between -180 and 180" in response.json()["detail"]


def test_upload_geojson_with_invalid_latitude(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify that GeoJSON with invalid latitude coordinates is rejected."""

    # Test with invalid latitude (outside -90 to 90 range)
    invalid_latitude_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [120.0, -95.0],  # Invalid latitude: -95 < -90
                            [121.0, -95.0],
                            [121.0, -94.0],
                            [120.0, -94.0],
                            [120.0, -95.0],
                        ],
                    ],
                },
                "properties": {"name": "test_polygon"},
            }
        ],
    }

    # Create a file-like object with the GeoJSON data
    geojson_file = BytesIO(json.dumps(invalid_latitude_geojson).encode())

    response = client.post(
        f"{settings.API_V1_STR}/locations/upload_project_boundary",
        files={"files": ("test.geojson", geojson_file, "application/json")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid latitude -95" in response.json()["detail"]
    assert "Must be between -90 and 90" in response.json()["detail"]


def test_upload_geojson_with_valid_coordinates(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify that GeoJSON with valid geographic coordinates is accepted."""

    # Test with valid coordinates
    valid_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [120.0, 40.0],  # Valid coordinates
                            [121.0, 40.0],
                            [121.0, 41.0],
                            [120.0, 41.0],
                            [120.0, 40.0],
                        ],
                    ],
                },
                "properties": {"name": "test_polygon"},
            }
        ],
    }

    # Create a file-like object with the GeoJSON data
    geojson_file = BytesIO(json.dumps(valid_geojson).encode())

    response = client.post(
        f"{settings.API_V1_STR}/locations/upload_project_boundary",
        files={"files": ("test.geojson", geojson_file, "application/json")},
    )
    assert response.status_code == status.HTTP_200_OK
    fc = response.json()
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) > 0
    assert fc["features"][0]["geometry"]["type"] == "Polygon"


def test_upload_single_feature_with_invalid_coordinates(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify that single Feature (not FeatureCollection) with invalid coordinates is rejected."""

    # Test with invalid coordinates in a single Feature (not FeatureCollection)
    invalid_feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [200.0, 45.0],  # Invalid longitude: 200 > 180
                    [201.0, 45.0],
                    [201.0, 46.0],
                    [200.0, 46.0],
                    [200.0, 45.0],
                ],
            ],
        },
        "properties": {"name": "test_polygon"},
    }

    # Create a file-like object with the GeoJSON data
    geojson_file = BytesIO(json.dumps(invalid_feature).encode())

    response = client.post(
        f"{settings.API_V1_STR}/locations/upload_project_boundary",
        files={"files": ("test.geojson", geojson_file, "application/json")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid longitude 200" in response.json()["detail"]
    assert "Must be between -180 and 180" in response.json()["detail"]


def test_handle_geojson_point_invalid_coordinates() -> None:
    """Test coordinate validation for Point geometry by calling handle_geojson directly."""
    from app.api.api_v1.endpoints.locations import handle_geojson
    from fastapi import HTTPException

    # Test Point with invalid longitude
    invalid_point = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [200.0, 45.0],  # Invalid longitude: 200 > 180
        },
        "properties": {"name": "test_point"},
    }

    # Create a file-like object with the GeoJSON data
    geojson_file = BytesIO(json.dumps(invalid_point).encode())

    # Should raise HTTPException with coordinate validation error
    with pytest.raises(HTTPException) as exc_info:
        handle_geojson(geojson_file)

    assert exc_info.value.status_code == 400
    assert "Invalid longitude 200" in str(exc_info.value.detail)
    assert "Must be between -180 and 180" in str(exc_info.value.detail)


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
