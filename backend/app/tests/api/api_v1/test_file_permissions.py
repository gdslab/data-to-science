from datetime import datetime

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.file_permission import create_file_permission


def test_create_file_permission(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}"
        f"/file_permission",
    )
    assert response.status_code == status.HTTP_201_CREATED
    file_permission = response.json()
    assert file_permission["access"] == "RESTRICTED"
    assert file_permission["file_id"] == str(data_product.obj.id)
    expires_at = datetime.strptime(
        file_permission["expires_at"], "%Y-%m-%dT%H:%M:%S.%f"
    )
    created_at = datetime.strptime(
        file_permission["created_at"], "%Y-%m-%dT%H:%M:%S.%f"
    )
    assert (expires_at - created_at).days == 7


def test_update_file_permission(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    file_permission = create_file_permission(db, file_id=data_product.obj.id)
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
