from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.tests.utils.breedbase_connection import create_breedbase_connection
from app.tests.utils.project import create_project


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
        "trial_id": "1234567890",
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
    assert response_data["trial_id"] == payload["trial_id"]
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
    assert response_data["trial_id"] == breedbase_connection.trial_id
    assert response_data["base_url"] == breedbase_connection.base_url


def test_get_breedbase_connection_by_trial_id(
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

    # Get breedbase connection by trial ID
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/breedbase-connections/trial/{breedbase_connection.trial_id}"
    )

    # Verify that the breedbase connection was read
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data is not None
    assert response_data["project_id"] == str(project.id)
    assert response_data["trial_id"] == breedbase_connection.trial_id
    assert response_data["base_url"] == breedbase_connection.base_url


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

    # New trial ID
    new_trial_id = "1111111111"

    # Update breedbase connection payload
    payload = {
        "trial_id": new_trial_id,
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
    assert response_data["trial_id"] == new_trial_id
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
    assert response_data["trial_id"] == breedbase_connection.trial_id
    assert response_data["base_url"] == breedbase_connection.base_url

    # Get breedbase connection from database
    breedbase_connection_from_db = crud.breedbase_connection.get(
        db, id=breedbase_connection.id
    )

    # Verify that the breedbase connection was removed
    assert breedbase_connection_from_db is None
