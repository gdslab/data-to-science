from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.tests.conftest import pytest_requires_breedbase
from app.tests.utils.breedbase_connection import create_breedbase_connection
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user


@pytest_requires_breedbase
def test_create_breedbase_connection(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Get current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )

    # Create project
    project = create_project(db, owner_id=current_user.id)

    # Breedbase connection payload
    payload = {
        "base_url": "https://example.com",
        "study_id": "1234567890",
    }

    # Create breedbase connection
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/breedbase-connections",
        json=payload,
    )

    # Verify that the breedbase connection was created
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data is not None
    assert response_data["project_id"] == str(project.id)
    assert response_data["study_id"] == payload["study_id"]
    assert response_data["base_url"] == payload["base_url"]


@pytest_requires_breedbase
def test_read_breedbase_connection(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Get current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )

    # Create project
    project = create_project(db, owner_id=current_user.id)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # Read breedbase connection
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/breedbase-connections/{breedbase_connection.id}"
    )

    # Verify that the breedbase connection was read
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data is not None
    assert response_data["project_id"] == str(project.id)
    assert response_data["study_id"] == breedbase_connection.study_id
    assert response_data["base_url"] == breedbase_connection.base_url


@pytest_requires_breedbase
def test_read_breedbase_connections(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Get current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )

    # Create project
    project = create_project(db, owner_id=current_user.id)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)
    breedbase_connection_id = str(breedbase_connection.id)

    # Create another breedbase connection
    breedbase_connection_2 = create_breedbase_connection(db, project.id)
    breedbase_connection_2_id = str(breedbase_connection_2.id)

    # Read breedbase connections
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/breedbase-connections"
    )

    # Verify that the breedbase connections were read
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data is not None
    assert len(response_data) == 2
    assert breedbase_connection_id in [connection["id"] for connection in response_data]
    assert breedbase_connection_2_id in [
        connection["id"] for connection in response_data
    ]


@pytest_requires_breedbase
def test_get_breedbase_connection_by_study_id(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Get current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )

    # Create project
    project = create_project(db, owner_id=current_user.id)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # Get breedbase connection by study ID
    response = client.get(
        f"{settings.API_V1_STR}/breedbase-connections/study/{breedbase_connection.study_id}"
    )

    # Verify that the breedbase connection was read
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data is not None
    assert len(response_data) == 1
    assert response_data[0]["project_id"] == str(project.id)
    assert response_data[0]["study_id"] == breedbase_connection.study_id
    assert response_data[0]["base_url"] == breedbase_connection.base_url

    # Create another project with the same study_id
    project2 = create_project(db, owner_id=current_user.id)
    breedbase_connection2 = create_breedbase_connection(
        db, project2.id, study_id=breedbase_connection.study_id
    )

    # Get all breedbase connections for the study_id
    response = client.get(
        f"{settings.API_V1_STR}/breedbase-connections/study/{breedbase_connection.study_id}"
    )

    # Verify that both connections were read
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data is not None
    assert len(response_data) == 2
    connection_ids = [conn["id"] for conn in response_data]
    assert str(breedbase_connection.id) in connection_ids
    assert str(breedbase_connection2.id) in connection_ids


@pytest_requires_breedbase
def test_get_breedbase_connection_by_study_id_unauthorized(
    client: TestClient, db: Session
) -> None:
    # Create project
    project = create_project(db)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # Try to get breedbase connection by study ID without auth
    response = client.get(
        f"{settings.API_V1_STR}/breedbase-connections/study/{breedbase_connection.study_id}"
    )

    # Verify unauthorized response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest_requires_breedbase
def test_get_breedbase_connection_by_study_id_wrong_user(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Create project with a different user
    other_user = create_user(db)
    project = create_project(db, owner_id=other_user.id)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # Try to get breedbase connection by study ID with different user
    response = client.get(
        f"{settings.API_V1_STR}/breedbase-connections/study/{breedbase_connection.study_id}",
    )

    # Verify empty result (since user doesn't have access to any projects with this study_id)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data == []


@pytest_requires_breedbase
def test_update_breedbase_connection(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Get current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )

    # Create project
    project = create_project(db, owner_id=current_user.id)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # New study ID
    new_study_id = "1111111111"

    # Update breedbase connection payload
    payload = {
        "study_id": new_study_id,
    }

    # Update breedbase connection
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/breedbase-connections/{breedbase_connection.id}",
        json=payload,
    )

    # Verify that the breedbase connection was updated
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data is not None
    assert response_data["project_id"] == str(project.id)
    assert response_data["study_id"] == new_study_id
    assert response_data["base_url"] == breedbase_connection.base_url


@pytest_requires_breedbase
def test_remove_breedbase_connection(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Get current user
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_access_token),
    )

    # Create project
    project = create_project(db, owner_id=current_user.id)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # Remove breedbase connection
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/breedbase-connections/{breedbase_connection.id}"
    )

    # Verify that the breedbase connection was removed
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data is not None
    assert response_data["project_id"] == str(project.id)
    assert response_data["study_id"] == breedbase_connection.study_id
    assert response_data["base_url"] == breedbase_connection.base_url

    # Get breedbase connection from database
    breedbase_connection_from_db = crud.breedbase_connection.get(
        db, id=breedbase_connection.id
    )

    # Verify that the breedbase connection was removed
    assert breedbase_connection_from_db is None


def _mock_httpx_response(status_code=200, json_data=None):
    """Create a mock httpx response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    return mock_response


@pytest_requires_breedbase
@patch("app.api.api_v1.endpoints.breedbase_connections.httpx.AsyncClient")
@patch(
    "app.api.api_v1.endpoints.breedbase_connections.socket.getaddrinfo",
    return_value=[(2, 1, 6, "", ("93.184.216.34", 0))],
)
def test_brapi_proxy_get(
    mock_getaddrinfo,
    mock_async_client_cls,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    mock_response = _mock_httpx_response(
        json_data={"result": {"data": [{"studyDbId": "123"}]}}
    )
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    payload = {
        "url": "https://example.com/brapi/v2/studies",
        "method": "GET",
    }

    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json=payload,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"result": {"data": [{"studyDbId": "123"}]}}
    mock_client.get.assert_called_once()


@pytest_requires_breedbase
@patch("app.api.api_v1.endpoints.breedbase_connections.httpx.AsyncClient")
@patch(
    "app.api.api_v1.endpoints.breedbase_connections.socket.getaddrinfo",
    return_value=[(2, 1, 6, "", ("93.184.216.34", 0))],
)
def test_brapi_proxy_post_with_token(
    mock_getaddrinfo,
    mock_async_client_cls,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    mock_response = _mock_httpx_response(
        status_code=202,
        json_data={"result": {"searchResultsDbId": "abc123"}},
    )
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    payload = {
        "url": "https://example.com/brapi/v2/search/studies",
        "method": "POST",
        "body": {"studyDbIds": ["123"]},
        "brapi_token": "test-token-abc",
    }

    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json=payload,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"result": {"searchResultsDbId": "abc123"}}

    # Verify the Authorization header was passed
    call_kwargs = mock_client.post.call_args
    assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer test-token-abc"


@pytest_requires_breedbase
def test_brapi_proxy_unauthorized(
    client: TestClient, db: Session
) -> None:
    # Remove auth token to simulate unauthenticated request
    client.headers.pop("Authorization", None)
    payload = {
        "url": "https://example.com/brapi/v2/studies",
        "method": "GET",
    }

    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json=payload,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest_requires_breedbase
def test_brapi_proxy_rejects_non_brapi_url(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    payload = {
        "url": "https://example.com/api/v1/users",
        "method": "GET",
    }

    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json=payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "brapi" in response.json()["detail"].lower()


@pytest_requires_breedbase
def test_brapi_proxy_rejects_private_ip(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    payload = {
        "url": "http://127.0.0.1/brapi/v2/studies",
        "method": "GET",
    }

    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json=payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "private" in response.json()["detail"].lower()


@pytest_requires_breedbase
@patch(
    "app.api.api_v1.endpoints.breedbase_connections.settings.BREEDBASE_ALLOWED_HOSTS",
    "allowed-host.example.com",
)
def test_brapi_proxy_rejects_unlisted_host(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    payload = {
        "url": "https://not-allowed.example.com/brapi/v2/studies",
        "method": "GET",
    }

    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json=payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "allowed" in response.json()["detail"].lower()


@pytest_requires_breedbase
def test_brapi_proxy_rejects_invalid_method(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    payload = {
        "url": "https://example.com/brapi/v2/studies",
        "method": "DELETE",
    }

    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json=payload,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest_requires_breedbase
@patch(
    "app.api.api_v1.endpoints.breedbase_connections.socket.getaddrinfo",
    return_value=[(2, 1, 6, "", ("93.184.216.34", 0))],
)
@patch("app.api.api_v1.endpoints.breedbase_connections.httpx.AsyncClient")
def test_brapi_proxy_connect_timeout(
    mock_async_client_cls,
    mock_getaddrinfo,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectTimeout("Connection timed out"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    payload = {
        "url": "https://example.com/brapi/v2/studies",
        "method": "GET",
    }

    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json=payload,
    )

    assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    assert "timed out" in response.json()["detail"].lower()


@pytest_requires_breedbase
@patch(
    "app.api.api_v1.endpoints.breedbase_connections.socket.getaddrinfo",
    return_value=[(2, 1, 6, "", ("93.184.216.34", 0))],
)
@patch("app.api.api_v1.endpoints.breedbase_connections.httpx.AsyncClient")
def test_brapi_proxy_read_timeout(
    mock_async_client_cls,
    mock_getaddrinfo,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ReadTimeout("Read timed out"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    payload = {
        "url": "https://example.com/brapi/v2/studies",
        "method": "GET",
    }

    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json=payload,
    )

    assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    assert "too long to respond" in response.json()["detail"].lower()


@pytest_requires_breedbase
@patch(
    "app.api.api_v1.endpoints.breedbase_connections.socket.getaddrinfo",
    return_value=[(2, 1, 6, "", ("93.184.216.34", 0))],
)
@patch("app.api.api_v1.endpoints.breedbase_connections.httpx.AsyncClient")
def test_brapi_proxy_connect_error(
    mock_async_client_cls,
    mock_getaddrinfo,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    payload = {
        "url": "https://example.com/brapi/v2/studies",
        "method": "GET",
    }

    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json=payload,
    )

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert "could not connect" in response.json()["detail"].lower()


@pytest_requires_breedbase
@patch(
    "app.api.api_v1.endpoints.breedbase_connections.socket.getaddrinfo",
    return_value=[(2, 1, 6, "", ("93.184.216.34", 0))],
)
@patch("app.api.api_v1.endpoints.breedbase_connections.httpx.AsyncClient")
def test_brapi_proxy_generic_http_error(
    mock_async_client_cls,
    mock_getaddrinfo,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Something went wrong"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    payload = {
        "url": "https://example.com/brapi/v2/studies",
        "method": "GET",
    }

    response = client.post(
        f"{settings.API_V1_STR}/breedbase/brapi/proxy",
        json=payload,
    )

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert "error communicating" in response.json()["detail"].lower()
