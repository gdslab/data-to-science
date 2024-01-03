from datetime import datetime

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project_member import create_project_member


def test_update_file_permission_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.obj.id
    )
    updated_data = {"access": "UNRESTRICTED"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
        f"/file_permission",
        json=updated_data,
    )
    assert response.status_code == status.HTTP_200_OK
    updated_file_permission = response.json()
    assert updated_file_permission["id"] == str(file_permission.id)
    assert updated_file_permission["file_id"] == str(file_permission.file_id)
    assert updated_file_permission["access"] == "UNRESTRICTED"


def test_update_file_permission_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role="manager",
    )
    updated_data = {"access": "UNRESTRICTED"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
        f"/file_permission",
        json=updated_data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_file_permission_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role="viewer",
    )
    updated_data = {"access": "UNRESTRICTED"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
        f"/file_permission",
        json=updated_data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_file_permission_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    data_product = SampleDataProduct(db)
    updated_data = {"access": "UNRESTRICTED"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
        f"/file_permission",
        json=updated_data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
