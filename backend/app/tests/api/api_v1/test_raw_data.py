import os
import shutil

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.project import create_random_project
from app.tests.utils.flight import create_flight
from app.tests.utils.raw_data import create_raw_data


def test_create_raw_data(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify file is uploaded, renamed, and stored on local disk."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_random_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    geotiff = os.path.join(os.sep, "app", "app", "tests", "utils", "./test.tif")
    with open(geotiff, "rb") as data:
        files = {"files": data}
        project_url = f"{settings.API_V1_STR}/projects/{flight.project_id}"
        r = client.post(f"{project_url}/flights/{flight.id}/raw_data", files=files)
        assert r.status_code == 200
    shutil.rmtree(os.path.join(os.sep, "tmp", "testing"))


def test_get_raw_data(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify retrieval of raw data user can access."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_random_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    raw_data = create_raw_data(db, flight=flight)
    project_url = f"{settings.API_V1_STR}/projects/{project.id}"
    r = client.get(f"{project_url}/flights/{flight.id}/raw_data/{raw_data.id}")
    assert 200 == r.status_code
    response = r.json()
    assert str(raw_data.id) == response["id"]
    assert "original_filename" in response
    assert "url" in response


def test_get_all_raw_data(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify retreival of all raw data user can access."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_random_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    create_raw_data(db, flight=flight)
    create_raw_data(db, flight=flight)
    create_raw_data(db, flight=flight)
    create_raw_data(db)
    flight_url = f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}"
    r = client.get(f"{flight_url}/raw_data")
    assert 200 == r.status_code
    all_raw_data = r.json()
    assert type(all_raw_data) is list
    assert len(all_raw_data) == 3
    for raw_data in all_raw_data:
        assert "flight_id" in raw_data
        assert raw_data["flight_id"] == str(flight.id)
        assert "original_filename" in raw_data
        assert "url" in raw_data
