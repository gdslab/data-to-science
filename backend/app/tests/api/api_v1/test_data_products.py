import os
import shutil

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.data_product import create_data_product
from app.tests.utils.project import create_random_project
from app.tests.utils.flight import create_flight


def test_create_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify file is uploaded, renamed, and stored on local disk."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_random_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    geotiff = os.path.join(os.sep, "app", "app", "tests", "data", "test.tif")
    with open(geotiff, "rb") as data:
        files = {"files": data}
        project_url = f"{settings.API_V1_STR}/projects/{flight.project_id}"
        r = client.post(
            f"{project_url}/flights/{flight.id}/data_products",
            params={"dtype": "dsm"},
            files=files,
        )
        assert r.status_code == 202
    shutil.rmtree(os.path.join(os.sep, "tmp", "testing"))


def test_get_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify retrieval of data product user can access."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_random_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = create_data_product(db, flight=flight)
    project_url = f"{settings.API_V1_STR}/projects/{project.id}"
    r = client.get(f"{project_url}/flights/{flight.id}/data_products/{data_product.id}")
    assert 200 == r.status_code
    response = r.json()
    assert str(data_product.id) == response["id"]
    assert "band_info" in response
    assert "data_type" in response
    # assert "filepath" not in response
    assert "flight_id" in response
    assert "original_filename" in response
    assert "url" in response
    assert "status" in response


def test_get_all_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Verify retreival of all data product user can access."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_random_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    create_data_product(db, flight=flight)
    create_data_product(db, flight=flight)
    create_data_product(db, flight=flight)
    create_data_product(db)
    flight_url = f"{settings.API_V1_STR}/projects/{project.id}/flights/{flight.id}"
    r = client.get(f"{flight_url}/data_products")
    assert 200 == r.status_code
    response = r.json()
    assert type(response) is list
    assert len(response) == 3
    for data_product in response:
        assert data_product["flight_id"] == str(flight.id)
        assert "band_info" in data_product
        assert "data_type" in data_product
        # assert "filepath" not in data_product
        assert "flight_id" in data_product
        assert "original_filename" in data_product
        assert "url" in data_product
