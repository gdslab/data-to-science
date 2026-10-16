from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.enums.api_key_scope import (
    ALL_API_KEY_SCOPES,
    MAX_ACTIVE_API_KEYS,
    APIKeyScope,
)
from app.schemas.role import Role
from app.schemas.user import UserUpdate
from app.tests.conftest import pytest_requires_breedbase
from app.tests.utils.breedbase_connection import create_breedbase_connection
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.raw_data import SampleRawData
from app.tests.utils.user import create_user
from app.utils.ProtectedStaticFiles import (
    verify_api_key_raw_data_access,
    verify_api_key_static_file_access,
)

API_KEYS_URL = f"{settings.API_V1_STR}/api-keys"


# Tests for API key management endpoints


def test_create_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    response = client.post(
        API_KEYS_URL, json={"name": "  qgis  ", "scopes": ["read", "read"]}
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["api_key"]
    assert response_data["name"] == "qgis"
    assert response_data["scopes"] == ["read"]
    assert response_data["user_id"] == str(current_user.id)
    api_key_in_db = crud.api_key.get_by_api_key(db, api_key=response_data["api_key"])
    assert api_key_in_db
    assert api_key_in_db.is_active


def test_create_api_key_without_name(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    response = client.post(API_KEYS_URL, json={"scopes": ["create"]})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] is None
    assert response.json()["scopes"] == ["create"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"scopes": []},
        {"scopes": ["admin"]},
        {"scopes": ["write"]},
        {"scopes": ["read"], "name": "x" * 65},
    ],
)
def test_create_api_key_with_invalid_payload(
    client: TestClient, db: Session, normal_user_access_token: str, payload: dict
) -> None:
    response = client.post(API_KEYS_URL, json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_api_key_by_demo_user(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    crud.user.update(db, db_obj=current_user, obj_in=UserUpdate(is_demo=True))
    response = client.post(API_KEYS_URL, json={"scopes": ["read"]})
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_api_key_over_limit(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    for _ in range(MAX_ACTIVE_API_KEYS):
        crud.api_key.create_with_user(
            db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
        )
    response = client.post(API_KEYS_URL, json={"scopes": ["read"]})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        crud.api_key.count_active_by_user(db, user_id=current_user.id)
        == MAX_ACTIVE_API_KEYS
    )


def test_create_api_key_after_revoking_at_limit(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    api_keys = [
        crud.api_key.create_with_user(
            db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
        )
        for _ in range(MAX_ACTIVE_API_KEYS)
    ]
    crud.api_key.deactivate(db, api_key_id=api_keys[0].id, user_id=current_user.id)
    response = client.post(API_KEYS_URL, json={"scopes": ["read"]})
    assert response.status_code == status.HTTP_201_CREATED


def test_read_api_keys(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    other_user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=[APIKeyScope.READ], name="qgis"
    )
    revoked_api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
    )
    crud.api_key.deactivate(db, api_key_id=revoked_api_key.id, user_id=current_user.id)
    crud.api_key.create_with_user(db, user_id=other_user.id, scopes=ALL_API_KEY_SCOPES)
    response = client.get(API_KEYS_URL)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["id"] == str(api_key.id)
    assert response_data[0]["name"] == "qgis"
    assert response_data[0]["scopes"] == ["read"]


def test_update_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=[APIKeyScope.READ]
    )
    response = client.patch(
        f"{API_KEYS_URL}/{api_key.id}",
        json={"name": "device", "scopes": ["create", "update"]},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "device"
    assert response.json()["scopes"] == ["create", "update"]
    api_key_in_db = crud.api_key.get(db, id=api_key.id)
    assert api_key_in_db
    assert api_key_in_db.scopes == ["create", "update"]


def test_rename_and_clear_api_key_name(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=[APIKeyScope.READ], name="qgis"
    )
    response = client.patch(
        f"{API_KEYS_URL}/{api_key.id}", json={"name": "  field laptop  "}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "field laptop"
    assert response.json()["scopes"] == ["read"]
    # the profile page sends null when the name field is emptied
    response = client.patch(f"{API_KEYS_URL}/{api_key.id}", json={"name": None})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] is None
    api_key_in_db = crud.api_key.get(db, id=api_key.id)
    assert api_key_in_db
    assert api_key_in_db.name is None
    assert api_key_in_db.scopes == ["read"]


def test_update_api_key_with_empty_scopes(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=[APIKeyScope.READ]
    )
    response = client.patch(f"{API_KEYS_URL}/{api_key.id}", json={"scopes": []})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_api_key_owned_by_other_user(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    other_user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=other_user.id, scopes=[APIKeyScope.READ]
    )
    response = client.patch(
        f"{API_KEYS_URL}/{api_key.id}", json={"scopes": ALL_API_KEY_SCOPES}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_revoked_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=[APIKeyScope.READ]
    )
    crud.api_key.deactivate(db, api_key_id=api_key.id, user_id=current_user.id)
    response = client.patch(f"{API_KEYS_URL}/{api_key.id}", json={"name": "x"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_revoke_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
    )
    response = client.delete(f"{API_KEYS_URL}/{api_key.id}")
    assert response.status_code == status.HTTP_200_OK
    api_key_in_db = crud.api_key.get(db, id=api_key.id)
    assert api_key_in_db
    assert not api_key_in_db.is_active
    # revoking an already revoked key
    response = client.delete(f"{API_KEYS_URL}/{api_key.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_revoke_api_key_by_demo_user(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
    )
    crud.user.update(db, db_obj=current_user, obj_in=UserUpdate(is_demo=True))
    response = client.delete(f"{API_KEYS_URL}/{api_key.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_revoke_api_key_owned_by_other_user(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    other_user = create_user(db)
    api_key = crud.api_key.create_with_user(
        db, user_id=other_user.id, scopes=ALL_API_KEY_SCOPES
    )
    response = client.delete(f"{API_KEYS_URL}/{api_key.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    api_key_in_db = crud.api_key.get(db, id=api_key.id)
    assert api_key_in_db
    assert api_key_in_db.is_active


def test_revoke_api_key_that_does_not_exist(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    response = client.delete(f"{API_KEYS_URL}/{uuid4()}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_api_key_endpoints_reject_api_key_auth(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    # keys are managed with a logged in session only
    response = client.get(API_KEYS_URL, headers={"X-API-KEY": normal_user_api_key})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Tests for API key scopes

READ = APIKeyScope.READ
CREATE = APIKeyScope.CREATE
UPDATE = APIKeyScope.UPDATE
DELETE = APIKeyScope.DELETE


def create_user_api_key(db: Session, scopes: list[APIKeyScope]) -> tuple:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(db, user_id=user.id, scopes=scopes)
    return user, api_key.api_key


def scope_error(scope: APIKeyScope) -> str:
    return f"API key does not have the '{scope.value}' scope"


def test_read_scope_allows_get_request(client: TestClient, db: Session) -> None:
    user, api_key = create_user_api_key(db, [READ])
    project = create_project(db, owner_id=user.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}",
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    # usage is recorded for header requests, not only static file requests
    api_key_obj = crud.api_key.get_by_api_key(db, api_key=api_key)
    assert api_key_obj
    assert api_key_obj.last_used_at
    assert api_key_obj.total_requests == 1


def test_rejected_request_does_not_record_use(client: TestClient, db: Session) -> None:
    user, api_key = create_user_api_key(db, [CREATE])
    project = create_project(db, owner_id=user.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}",
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    api_key_obj = crud.api_key.get_by_api_key(db, api_key=api_key)
    assert api_key_obj
    assert api_key_obj.last_used_at is None
    assert api_key_obj.total_requests == 0


@pytest.mark.parametrize("scopes", [[CREATE], [UPDATE], [DELETE]])
def test_get_request_requires_read_scope(
    client: TestClient, db: Session, scopes: list[APIKeyScope]
) -> None:
    user, api_key = create_user_api_key(db, scopes)
    project = create_project(db, owner_id=user.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}",
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == scope_error(READ)


def test_create_scope_allows_optional_auth_post_request(
    client: TestClient, db: Session
) -> None:
    user, api_key = create_user_api_key(db, [CREATE])
    data_product = SampleDataProduct(db, user=user)
    response = client.post(
        f"{settings.API_V1_STR}/public/data_products/{data_product.obj.id}/view",
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize("scopes", [[READ], [UPDATE], [DELETE]])
def test_optional_auth_post_request_requires_create_scope(
    client: TestClient, db: Session, scopes: list[APIKeyScope]
) -> None:
    user, api_key = create_user_api_key(db, scopes)
    data_product = SampleDataProduct(db, user=user)
    response = client.post(
        f"{settings.API_V1_STR}/public/data_products/{data_product.obj.id}/view",
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == scope_error(CREATE)


@pytest_requires_breedbase
def test_create_scope_allows_post_request(client: TestClient, db: Session) -> None:
    user, api_key = create_user_api_key(db, [CREATE])
    project = create_project(db, owner_id=user.id)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/breedbase-connections",
        json={"base_url": "https://example.com", "study_id": "1234567890"},
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest_requires_breedbase
@pytest.mark.parametrize("scopes", [[READ], [UPDATE], [DELETE]])
def test_post_request_requires_create_scope(
    client: TestClient, db: Session, scopes: list[APIKeyScope]
) -> None:
    user, api_key = create_user_api_key(db, scopes)
    project = create_project(db, owner_id=user.id)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/breedbase-connections",
        json={"base_url": "https://example.com", "study_id": "1234567890"},
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == scope_error(CREATE)


@pytest_requires_breedbase
def test_update_scope_allows_put_request(client: TestClient, db: Session) -> None:
    user, api_key = create_user_api_key(db, [UPDATE])
    project = create_project(db, owner_id=user.id)
    connection = create_breedbase_connection(db, project_id=project.id)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/breedbase-connections/{connection.id}",
        json={"study_id": "0987654321"},
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["study_id"] == "0987654321"


@pytest_requires_breedbase
@pytest.mark.parametrize("scopes", [[READ], [CREATE], [DELETE]])
def test_put_request_requires_update_scope(
    client: TestClient, db: Session, scopes: list[APIKeyScope]
) -> None:
    user, api_key = create_user_api_key(db, scopes)
    project = create_project(db, owner_id=user.id)
    connection = create_breedbase_connection(db, project_id=project.id)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/breedbase-connections/{connection.id}",
        json={"study_id": "0987654321"},
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == scope_error(UPDATE)
    connection_in_db = crud.breedbase_connection.get(db, id=connection.id)
    assert connection_in_db
    assert connection_in_db.study_id == "1234567890"


@pytest_requires_breedbase
def test_delete_scope_allows_delete_request(client: TestClient, db: Session) -> None:
    user, api_key = create_user_api_key(db, [DELETE])
    project = create_project(db, owner_id=user.id)
    connection = create_breedbase_connection(db, project_id=project.id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/breedbase-connections/{connection.id}",
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    assert crud.breedbase_connection.get(db, id=connection.id) is None


@pytest_requires_breedbase
@pytest.mark.parametrize("scopes", [[READ], [CREATE], [UPDATE]])
def test_delete_request_requires_delete_scope(
    client: TestClient, db: Session, scopes: list[APIKeyScope]
) -> None:
    user, api_key = create_user_api_key(db, scopes)
    project = create_project(db, owner_id=user.id)
    connection = create_breedbase_connection(db, project_id=project.id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}"
        f"/breedbase-connections/{connection.id}",
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == scope_error(DELETE)
    assert crud.breedbase_connection.get(db, id=connection.id)


@pytest_requires_breedbase
@patch("app.api.api_v1.endpoints.breedbase_connections.httpx.AsyncClient")
@patch(
    "app.api.api_v1.endpoints.breedbase_connections.socket.getaddrinfo",
    return_value=[(2, 1, 6, "", ("93.184.216.34", 0))],
)
def test_read_scope_allows_brapi_proxy_post(
    mock_getaddrinfo, mock_async_client_cls, client: TestClient, db: Session
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"data": []}}
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    _, api_key = create_user_api_key(db, [READ])
    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json={"url": "https://example.com/brapi/v2/studies", "method": "GET"},
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_200_OK


@pytest_requires_breedbase
def test_create_scope_rejects_brapi_proxy_post(client: TestClient, db: Session) -> None:
    _, api_key = create_user_api_key(db, [CREATE])
    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json={"url": "https://example.com/brapi/v2/studies", "method": "GET"},
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == scope_error(READ)


def test_static_data_product_requires_read_scope(db: Session) -> None:
    user, api_key = create_user_api_key(db, [CREATE, UPDATE, DELETE])
    data_product = SampleDataProduct(db, user=user)
    assert not verify_api_key_static_file_access(
        data_product=data_product.obj, api_key=api_key, db=db
    )


def test_static_raw_data_requires_read_scope(db: Session) -> None:
    user, api_key = create_user_api_key(db, [CREATE, UPDATE, DELETE])
    raw_data = SampleRawData(db, user=user)
    assert not verify_api_key_raw_data_access(
        raw_data=raw_data.obj, api_key=api_key, db=db
    )


# Tests for static file API key access


def test_access_authorized_data_product_with_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create user that will own project/data product
    project_owner = create_user(db)
    # user making request
    current_user = get_current_user(db, normal_user_access_token)
    # create api key for current_user
    current_user_api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
    )
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
    api_key_in_db = crud.api_key.get(db, id=current_user_api_key.id)
    assert api_key_in_db
    assert api_key_in_db.last_used_at
    assert api_key_in_db.total_requests == 1


def test_access_authorized_deactivated_data_product_with_api_key(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # create user that will own project/data product
    project_owner = create_user(db)
    # user making request
    current_user = get_current_user(db, normal_user_access_token)
    # create api key for current_user
    current_user_api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
    )
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
    with pytest.raises(HTTPException):
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
    current_user_api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
    )
    # create data product owned by current user
    data_product = SampleDataProduct(db, user=current_user)

    # verify with valid api key
    assert verify_api_key_static_file_access(
        data_product=data_product.obj, api_key=current_user_api_key.api_key, db=db
    )

    # deactivate api key
    deactivated_api_key = crud.api_key.deactivate(
        db, api_key_id=current_user_api_key.id, user_id=current_user.id
    )

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
    current_user_api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
    )
    # create data product owned by project owner user
    data_product = SampleDataProduct(db, user=project_owner)

    # current user does not have access to the data product project
    with pytest.raises(HTTPException):
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
    current_user_api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
    )
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
    current_user_api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
    )
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
    with pytest.raises(HTTPException):
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
    current_user_api_key = crud.api_key.create_with_user(
        db, user_id=current_user.id, scopes=ALL_API_KEY_SCOPES
    )
    # create raw data owned by project owner user
    raw_data = SampleRawData(db, user=project_owner)

    # current user does not have access to the raw data project
    with pytest.raises(HTTPException):
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
    api_key_obj = crud.api_key.get_by_api_key(db, api_key=normal_user_api_key)
    assert api_key_obj
    crud.api_key.deactivate(db, api_key_id=api_key_obj.id, user_id=current_user.id)

    # Create a project owned by this user
    sample = SampleDataProduct(db, user=current_user)

    # Try accessing with deactivated API key
    response = client.get(
        f"{settings.API_V1_STR}/projects/{sample.project.id}",
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
