from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.schemas.file_permission import FilePermissionUpdate
from app.tests.utils.data_product import SampleDataProduct


def test_read_public_data_product_bounds(client: TestClient, db: Session):
    # create data product owned by random user
    data_product = SampleDataProduct(db)
    # make data product public
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.obj.id
    )
    assert file_permission
    file_permission_in = FilePermissionUpdate(is_public=True)
    crud.file_permission.update(db, db_obj=file_permission, obj_in=file_permission_in)
    # get bounds for public data product
    response = client.get(
        f"{settings.API_V1_STR}/public/bounds?data_product_id={data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "bounds" in response_data
    response_bounds = response_data["bounds"] == [
        -86.94452647774037,
        41.44399199810876,
        -86.94442522789655,
        41.44408204910461,
    ]


def test_read_projected_data_product_bounds(client: TestClient, db: Session):
    # create data product owned by random user
    data_product = SampleDataProduct(db)
    # get bounds for public data product
    response = client.get(
        f"{settings.API_V1_STR}/public/bounds?data_product_id={data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_projected_data_product_bounds_with_authorized_user(
    client: TestClient, db: Session, normal_user_access_token: str
):
    # get current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token)
    )
    # create data product owned by logged in user
    data_product = SampleDataProduct(db, user=current_user)
    # get bounds for public data product
    response = client.get(
        f"{settings.API_V1_STR}/public/bounds?data_product_id={data_product.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "bounds" in response_data
    response_bounds = response_data["bounds"] == [
        -86.94452647774037,
        41.44399199810876,
        -86.94442522789655,
        41.44408204910461,
    ]
