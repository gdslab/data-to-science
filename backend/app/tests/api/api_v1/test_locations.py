import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings


def test_upload_shapefile_zip(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify uploaded shapefile zip is unpacked, read, and returned as GeoJSON."""
    shp_zip = os.path.join(os.sep, "app", "app", "tests", "data", "single_field.zip")
    with open(shp_zip, "rb") as data:
        files = {"files": data}
        r = client.post(f"{settings.API_V1_STR}/locations/upload", files=files)
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
        r = client.post(f"{settings.API_V1_STR}/locations/upload", files=files)
        assert r.status_code == 400
