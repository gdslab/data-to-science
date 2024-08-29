import requests
from datetime import datetime

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.user import UserUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.flight import create_flight
from app.tests.utils.user import create_user
from app.utils.ProtectedStaticFiles import verify_api_key_static_file_access


def test_request_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    response = client.get(f"{settings.API_V1_STR}/auth/request-api-key")
    assert response.status_code == status.HTTP_200_OK
    user_api_key = crud.api_key.get_by_user(db, user_id=current_user.id)
    assert user_api_key
    assert user_api_key.is_active


def test_request_api_key_by_demo_user(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    crud.user.update(db, db_obj=current_user, obj_in=UserUpdate(is_demo=True))
    response = client.get(f"{settings.API_V1_STR}/auth/request-api-key")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_revoke_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    api_key = crud.api_key.create_with_user(db, user_id=current_user.id)
    response = client.get(f"{settings.API_V1_STR}/auth/revoke-api-key")
    assert response.status_code == status.HTTP_200_OK
    api_key_in_db = crud.api_key.get(db, id=api_key.id)
    assert api_key_in_db
    assert not api_key_in_db.is_active


def test_revoke_api_key_by_demo_user(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    api_key = crud.api_key.create_with_user(db, user_id=current_user.id)
    crud.user.update(db, db_obj=current_user, obj_in=UserUpdate(is_demo=True))
    response = client.get(f"{settings.API_V1_STR}/auth/revoke-api-key")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_revoke_api_key_when_one_does_not_exist(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    response = client.get(f"{settings.API_V1_STR}/auth/revoke-api-key")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_access_authorized_data_product_with_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
):
    # create user that will own project/data product
    project_owner = create_user(db)
    # user making request
    current_user = get_current_user(db, normal_user_access_token)
    # create api key for current_user
    current_user_api_key = crud.api_key.create_with_user(db, user_id=current_user.id)
    # create data product owned by project owner user
    data_product = SampleDataProduct(db, user=project_owner)
    # project associated with data product
    project = data_product.project
    # add current user as member of project with default "viewer" role
    project_member = create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=project.id
    )

    # current user has access to the data product project
    assert verify_api_key_static_file_access(
        data_product=data_product.obj, api_key=current_user_api_key.api_key, db=db
    )


def test_access_authorized_deactivated_data_product_with_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
):
    # create user that will own project/data product
    project_owner = create_user(db)
    # user making request
    current_user = get_current_user(db, normal_user_access_token)
    # create api key for current_user
    current_user_api_key = crud.api_key.create_with_user(db, user_id=current_user.id)
    # create data product owned by project owner user
    data_product = SampleDataProduct(db, user=project_owner)
    # project associated with data product
    project = data_product.project
    # add current user as member of project with default "viewer" role
    project_member = create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=project.id
    )
    # deactivate data product
    deactivated_data_product = crud.data_product.deactivate(
        db, data_product_id=data_product.obj.id
    )

    # current user has access to the data product project, but data product deactivated
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key_static_file_access(
            data_product=deactivated_data_product,
            api_key=current_user_api_key.api_key,
            db=db,
        )


def test_access_authorized_data_product_with_deactivated_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
):
    # user making request
    current_user = get_current_user(db, normal_user_access_token)
    # create api key for current_user
    current_user_api_key = crud.api_key.create_with_user(db, user_id=current_user.id)
    # create data product owned by current user
    data_product = SampleDataProduct(db, user=current_user)

    # verify with valid api key
    assert verify_api_key_static_file_access(
        data_product=data_product.obj, api_key=current_user_api_key.api_key, db=db
    )

    # deactivate api key
    deactivated_api_key = crud.api_key.deactivate(db, user_id=current_user.id)

    # verify with deactivated api key
    assert not deactivated_api_key.is_active
    assert deactivated_api_key.deactivated_at < datetime.utcnow()
    assert not verify_api_key_static_file_access(
        data_product=data_product.obj, api_key=current_user_api_key.api_key, db=db
    )


def test_access_unauthorized_data_product_with_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
):
    # create user that will own project/data product
    project_owner = create_user(db)
    # user making request
    current_user = get_current_user(db, normal_user_access_token)
    # create api key for current_user
    current_user_api_key = crud.api_key.create_with_user(db, user_id=current_user.id)
    # create data product owned by project owner user
    data_product = SampleDataProduct(db, user=project_owner)

    # current user does not have access to the data product project
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key_static_file_access(
            data_product=data_product.obj,
            api_key=current_user_api_key.api_key,
            db=db,
        )
