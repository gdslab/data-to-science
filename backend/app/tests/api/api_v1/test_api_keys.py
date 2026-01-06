from datetime import datetime, timezone

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.role import Role
from app.schemas.user import UserUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project_member import create_project_member
from app.tests.utils.raw_data import SampleRawData
from app.tests.utils.user import create_user
from app.utils.ProtectedStaticFiles import (
    verify_api_key_raw_data_access,
    verify_api_key_static_file_access,
)


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
    crud.api_key.create_with_user(db, user_id=current_user.id)
    crud.user.update(db, db_obj=current_user, obj_in=UserUpdate(is_demo=True))
    response = client.get(f"{settings.API_V1_STR}/auth/revoke-api-key")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_revoke_api_key_when_one_does_not_exist(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    get_current_user(db, normal_user_access_token)
    response = client.get(f"{settings.API_V1_STR}/auth/revoke-api-key")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_access_authorized_data_product_with_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
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
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )

    # current user has access to the data product project
    assert verify_api_key_static_file_access(
        data_product=data_product.obj, api_key=current_user_api_key.api_key, db=db
    )


def test_access_authorized_deactivated_data_product_with_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
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
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )
    # deactivate data product
    deactivated_data_product = crud.data_product.deactivate(
        db, data_product_id=data_product.obj.id
    )
    assert deactivated_data_product

    # current user has access to the data product project, but data product deactivated
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key_static_file_access(
            data_product=deactivated_data_product,
            api_key=current_user_api_key.api_key,
            db=db,
        )


def test_access_authorized_data_product_with_deactivated_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
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
    assert deactivated_api_key
    assert not deactivated_api_key.is_active
    assert deactivated_api_key.deactivated_at.replace(
        tzinfo=timezone.utc
    ) < datetime.now(timezone.utc)
    assert not verify_api_key_static_file_access(
        data_product=data_product.obj, api_key=current_user_api_key.api_key, db=db
    )


def test_access_unauthorized_data_product_with_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
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


# Tests for RawData API key access


def test_access_authorized_raw_data_with_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test accessing authorized raw data with API key."""
    # create user that will own project/raw data
    project_owner = create_user(db)
    # user making request
    current_user = get_current_user(db, normal_user_access_token)
    # create api key for current_user
    current_user_api_key = crud.api_key.create_with_user(db, user_id=current_user.id)
    # create raw data owned by project owner user
    raw_data = SampleRawData(db, user=project_owner)
    # project associated with raw data
    project = raw_data.project
    # add current user as member of project with default "viewer" role
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )

    # current user has access to the raw data project
    assert verify_api_key_raw_data_access(
        raw_data=raw_data.obj, api_key=current_user_api_key.api_key, db=db
    )


def test_access_authorized_deactivated_raw_data_with_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test accessing authorized but deactivated raw data with API key."""
    # create user that will own project/raw data
    project_owner = create_user(db)
    # user making request
    current_user = get_current_user(db, normal_user_access_token)
    # create api key for current_user
    current_user_api_key = crud.api_key.create_with_user(db, user_id=current_user.id)
    # create raw data owned by project owner user
    raw_data = SampleRawData(db, user=project_owner)
    # project associated with raw data
    project = raw_data.project
    # add current user as member of project with default "viewer" role
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )
    # deactivate raw data
    deactivated_raw_data = crud.raw_data.deactivate(db, raw_data_id=raw_data.obj.id)
    assert deactivated_raw_data

    # current user has access to the raw data project, but raw data deactivated
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key_raw_data_access(
            raw_data=deactivated_raw_data,
            api_key=current_user_api_key.api_key,
            db=db,
        )


def test_access_unauthorized_raw_data_with_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test accessing unauthorized raw data with API key."""
    # create user that will own project/raw data
    project_owner = create_user(db)
    # user making request
    current_user = get_current_user(db, normal_user_access_token)
    # create api key for current_user
    current_user_api_key = crud.api_key.create_with_user(db, user_id=current_user.id)
    # create raw data owned by project owner user
    raw_data = SampleRawData(db, user=project_owner)

    # current user does not have access to the raw data project
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key_raw_data_access(
            raw_data=raw_data.obj, api_key=current_user_api_key.api_key, db=db
        )


# Tests for header-based API key authentication


def test_api_key_in_header(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    """Test that API key authentication works via X-API-KEY header."""
    # Get current user from API key
    current_user = crud.user.get_by_api_key(db, api_key=normal_user_api_key)
    assert current_user is not None

    # Create a project owned by this user
    sample = SampleDataProduct(db, user=current_user)

    # Try accessing a project endpoint with X-API-KEY header
    response = client.get(
        f"{settings.API_V1_STR}/projects/{sample.project.id}",
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    project_data = response.json()
    assert project_data["id"] == str(sample.project.id)


def test_api_key_in_header_invalid_key(client: TestClient, db: Session) -> None:
    """Test that invalid API key in header is rejected."""
    # Create a project
    owner = create_user(db)
    sample = SampleDataProduct(db, user=owner)

    # Try accessing with invalid API key
    response = client.get(
        f"{settings.API_V1_STR}/projects/{sample.project.id}",
        headers={"X-API-KEY": "invalid-api-key-12345"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_api_key_in_header_deactivated_key(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    """Test that deactivated API key in header is rejected."""
    # Get current user and deactivate their API key
    current_user = crud.user.get_by_api_key(db, api_key=normal_user_api_key)
    assert current_user is not None
    crud.api_key.deactivate(db, user_id=current_user.id)

    # Create a project owned by this user
    sample = SampleDataProduct(db, user=current_user)

    # Try accessing with deactivated API key
    response = client.get(
        f"{settings.API_V1_STR}/projects/{sample.project.id}",
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
