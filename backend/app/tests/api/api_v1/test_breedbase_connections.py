from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.tests.utils.breedbase_connection import create_breedbase_connection
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user


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
