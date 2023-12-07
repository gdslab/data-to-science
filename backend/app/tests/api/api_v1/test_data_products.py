import os
import shutil

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.flight import create_flight


def test_create_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    geotiff = os.path.join(os.sep, "app", "app", "tests", "data", "test.tif")
    with open(geotiff, "rb") as data:
        response = client.post(
            f"{settings.API_V1_STR}/projects/{flight.project_id}"
            f"/flights/{flight.id}/data_products",
            params={"dtype": "dsm"},
            files={"files": data},
        )

        assert response.status_code == 202

    shutil.rmtree(settings.TEST_STATIC_DIR)


def test_read_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True, user=current_user)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )

    assert 200 == response.status_code
    response_data_product = response.json()
    assert str(data_product.obj.id) == response_data_product["id"]
    assert "data_type" in response_data_product
    assert "flight_id" in response_data_product
    assert "original_filename" in response_data_product
    assert "stac_properties" in response_data_product
    assert "url" in response_data_product
    assert "status" in response_data_product
    assert "user_style" in response_data_product


def test_read_data_products(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleDataProduct(
            db,
            create_style=True,
            flight=flight,
            project=project,
            user=current_user,
        )
    SampleDataProduct(db)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{flight.id}/data_products"
    )

    assert 200 == response.status_code
    response_data_products = response.json()
    assert type(response_data_products) is list
    assert len(response_data_products) == 3
    for data_product in response_data_products:
        assert data_product["flight_id"] == str(flight.id)
        assert "data_type" in data_product
        assert "flight_id" in data_product
        assert "original_filename" in data_product
        assert "stac_properties" in data_product
        assert "url" in data_product
        assert "user_style" in data_product
