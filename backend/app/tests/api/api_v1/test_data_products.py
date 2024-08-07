import os
import shutil
from datetime import datetime

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.file_permission import FilePermissionUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.flight import create_flight
from app.tests.utils.user import create_user
from app.utils.ColorBar import create_outfilename


def test_read_data_product_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True, user=current_user)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert str(data_product.obj.id) == response_data_product["id"]
    assert "data_type" in response_data_product
    assert "flight_id" in response_data_product
    assert "original_filename" in response_data_product
    assert "stac_properties" in response_data_product
    assert "url" in response_data_product
    assert "initial_processing_status" in response_data_product
    assert "user_style" in response_data_product


def test_read_data_product_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role="manager",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert response_data_product["id"] == str(data_product.obj.id)


def test_read_data_product_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role="viewer",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert response_data_product["id"] == str(data_product.obj.id)


def test_read_data_product_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_public_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    data_product = SampleDataProduct(db).obj
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.id
    )
    assert file_permission
    file_permission_in_update = FilePermissionUpdate(is_public=True)
    crud.file_permission.update(
        db, db_obj=file_permission, obj_in=file_permission_in_update
    )
    response = client.get(f"{settings.API_V1_STR}/public?file_id={data_product.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data_product = response.json()
    assert response_data_product["id"] == str(data_product.id)


def test_read_restricted_data_product_with_public_url(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    data_product = SampleDataProduct(db).obj
    response = client.get(f"{settings.API_V1_STR}/public?file_id={data_product.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_generate_data_product_colorbar_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm", create_style=True)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role="viewer",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/utils/colorbar?cmin=100&cmax=200&cmap=terrain&refresh=false"
    )
    colorbar_filename = create_outfilename(100, 200, "terrain")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "colorbar_url" in response_data
    assert response_data["colorbar_url"] == (
        f"{settings.TEST_STATIC_DIR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/colorbars/{colorbar_filename}"
    )


def test_generate_data_product_colorbar_with_invalid_parameters(
    client: TestClient, db: Session, normal_user_access_token: str
):
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, data_type="dsm", create_style=True)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role="viewer",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/utils/colorbar?cmin=100&cmax=200&cmap=invalid-cmap&refresh=false"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_read_data_products_with_owner_role(
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
    assert response.status_code == status.HTTP_200_OK
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


def test_read_data_products_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleDataProduct(
            db,
            create_style=True,
            flight=flight,
            project=project,
            user=project_owner,
        )
    SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=project.id,
        role="manager",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{flight.id}/data_products"
    )
    assert response.status_code == status.HTTP_200_OK
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


def test_read_data_products_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleDataProduct(
            db,
            create_style=True,
            flight=flight,
            project=project,
            user=project_owner,
        )
    SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=project.id,
        role="viewer",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{flight.id}/data_products"
    )
    assert response.status_code == status.HTTP_200_OK
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


def test_read_data_products_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleDataProduct(
            db,
            create_style=True,
            flight=flight,
            project=project,
            user=project_owner,
        )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/flights/{flight.id}/data_products"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_deactivate_data_product_with_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
):
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True, user=current_user)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    deactivated_data_product = response.json()
    assert deactivated_data_product
    assert deactivated_data_product.get("id", None) == str(data_product.obj.id)
    assert deactivated_data_product.get("is_active", True) is False
    deactivated_at = datetime.strptime(
        deactivated_data_product.get("deactivated_at"), "%Y-%m-%dT%H:%M:%S.%f"
    )
    assert isinstance(deactivated_at, datetime)
    assert deactivated_at < datetime.utcnow()


def test_deactivate_data_product_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
):
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True)
    create_project_member(
        db,
        role="manager",
        member_id=current_user.id,
        project_id=data_product.project.id,
    )
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_data_product_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
):
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True)
    create_project_member(
        db,
        role="viewer",
        member_id=current_user.id,
        project_id=data_product.project.id,
    )
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_data_product_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
):
    data_product = SampleDataProduct(db, create_style=True)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_running_tool_on_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
):
    current_user = get_current_user(db, normal_user_access_token)
    rgb_data_product = SampleDataProduct(
        db, data_type="ortho", multispectral=True, user=current_user
    )
    processing_request = {
        "chm": False,
        "exg": True,
        "exgRed": 3,
        "exgGreen": 2,
        "exgBlue": 1,
        "ndvi": False,
        "ndviNIR": 4,
        "ndviRed": 3,
        "zonal": False,
        "zonal_layer_id": "",
    }

    response = client.post(
        f"{settings.API_V1_STR}/projects/{rgb_data_product.project.id}"
        f"/flights/{rgb_data_product.flight.id}/data_products/{rgb_data_product.obj.id}/tools",
        json=processing_request,
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
