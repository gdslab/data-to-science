from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.project_type import ProjectType
from app.schemas.indoor_project import IndoorProjectUpdate
from app.schemas.role import Role
from app.tests.utils.indoor_project import create_indoor_project
from app.tests.utils.project_member import create_project_member

API_URL = f"{settings.API_V1_STR}/indoor_projects"


def test_create_indoor_project(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test creating an indoor project with required and optional fields.
    """
    # indoor project form submission
    title = "Test Indoor Project"
    description = "Test indoor phenotyping project"
    start_date = datetime(2024, 4, 1)
    end_date = datetime(2024, 6, 30)

    # serialize start_date and end_date
    payload = {
        "title": title,
        "description": description,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    # post indoor project form data
    response = client.post(API_URL, json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert "id" in response_data
    assert response_data["title"] == title
    assert response_data["description"] == description
    assert response_data["start_date"] == start_date.isoformat()
    assert response_data["end_date"] == end_date.isoformat()
    assert "is_active" not in response_data
    assert "deactivated_at" not in response_data
    assert "owner_id" not in response_data


def test_create_indoor_project_with_invalid_date(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test creating an indoor project with invalid date value.
    """
    payload = {
        "title": "Invalid Date Test",
        "description": "This test should fail due to an invalid date",
        "start_date": "undefined",
        "end_date": datetime(2024, 3, 1).isoformat(),
    }

    # post indoor project form data
    response = client.post(API_URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_indoor_project_with_invalid_end_date(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test creating an indoor project with end date that comes before the start date.
    """
    payload = {
        "title": "Invalid end_date Test",
        "description": "This test should fail due to end_date being before start_date",
        "start_date": datetime(2024, 4, 1).isoformat(),
        "end_date": datetime(2024, 3, 1).isoformat(),
    }

    # post indoor project form data
    response = client.post(API_URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_read_indoor_project(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test reading an existing indoor project.
    """
    # create indoor project in database owned by current user
    current_user = get_current_user(db, normal_user_access_token)
    existing_indoor_project = create_indoor_project(db, owner_id=current_user.id)

    # get indoor project data
    response = client.get(f"{API_URL}/{existing_indoor_project.id}")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(existing_indoor_project.id)
    assert response_data["title"] == existing_indoor_project.title
    assert response_data["description"] == existing_indoor_project.description
    assert response_data["start_date"] == existing_indoor_project.start_date
    assert response_data["end_date"] == existing_indoor_project.end_date
    assert not hasattr(response_data, "is_active")
    assert not hasattr(response_data, "deactivated_at")
    assert not hasattr(response_data, "owner_id")


def test_read_indoor_project_without_permission(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test reading an existing indoor project without permission to access it.
    """
    # create indoor project in database owned by someone other than current user
    existing_indoor_project = create_indoor_project(db)

    # get indoor project data
    response = client.get(f"{API_URL}/{existing_indoor_project.id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    response_data = response.json()
    assert response_data["detail"]


def test_read_indoor_project_that_does_not_exist(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test reading an indoor project that does not exist.
    """
    # generate random UUID4
    missing_indoor_project_id = str(uuid4())

    # get indoor project data
    response = client.get(f"{API_URL}/{missing_indoor_project_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    response_data = response.json()
    assert response_data["detail"]


def test_read_indoor_projects(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test reading multiple existing indoor projects.
    """
    # create multiple indoor projects in database owned by current user
    current_user = get_current_user(db, normal_user_access_token)
    existing_indoor_project1 = create_indoor_project(db, owner_id=current_user.id)
    existing_indoor_project2 = create_indoor_project(db, owner_id=current_user.id)
    existing_indoor_project3 = create_indoor_project(db, owner_id=current_user.id)

    # get all indoor projects associated with current user
    response = client.get(f"{API_URL}")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, List)
    assert len(response_data) == 3
    for indoor_project in response_data:
        assert indoor_project["id"] in [
            str(existing_indoor_project1.id),
            str(existing_indoor_project2.id),
            str(existing_indoor_project3.id),
        ]


def test_read_indoor_project_as_manager(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test that a manager can read an indoor project.
    """
    # Create indoor project owned by someone else
    indoor_project = create_indoor_project(db)

    # Add current user as manager
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db,
        role=Role.MANAGER,
        member_id=current_user.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Get indoor project data
    response = client.get(f"{API_URL}/{indoor_project.id}")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(indoor_project.id)
    assert response_data["role"] == Role.MANAGER.value


def test_read_indoor_project_as_viewer(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test that a viewer can read an indoor project.
    """
    # Create indoor project owned by someone else
    indoor_project = create_indoor_project(db)

    # Add current user as viewer
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db,
        role=Role.VIEWER,
        member_id=current_user.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Get indoor project data
    response = client.get(f"{API_URL}/{indoor_project.id}")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(indoor_project.id)
    assert response_data["role"] == Role.VIEWER.value


def test_update_indoor_project_as_owner(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test updating an indoor project as owner.
    """
    # Create indoor project owned by current user
    current_user = get_current_user(db, normal_user_access_token)
    indoor_project = create_indoor_project(db, owner_id=current_user.id)

    # Update data
    update_data = jsonable_encoder(
        IndoorProjectUpdate(
            title="Updated Title",
            description="Updated Description",
            start_date=datetime(2024, 5, 1),
            end_date=datetime(2024, 10, 1),
        ).model_dump()
    )

    # Update indoor project
    response = client.put(f"{API_URL}/{indoor_project.id}", json=update_data)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(indoor_project.id)
    assert response_data["title"] == update_data["title"]
    assert response_data["description"] == update_data["description"]
    assert response_data["start_date"] == update_data["start_date"]
    assert response_data["end_date"] == update_data["end_date"]


def test_update_indoor_project_as_manager(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test updating an indoor project as manager.
    """
    # Create indoor project owned by someone else
    indoor_project = create_indoor_project(db)

    # Add current user as manager
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db,
        role=Role.MANAGER,
        member_id=current_user.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Update data
    update_data = jsonable_encoder(
        IndoorProjectUpdate(
            title="Updated by Manager",
            description="Updated Description",
        ).model_dump()
    )

    # Update indoor project
    response = client.put(f"{API_URL}/{indoor_project.id}", json=update_data)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["title"] == update_data["title"]
    assert response_data["description"] == update_data["description"]


def test_update_indoor_project_as_viewer(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test that a viewer cannot update an indoor project.
    """
    # Create indoor project owned by someone else
    indoor_project = create_indoor_project(db)

    # Add current user as viewer
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db,
        role=Role.VIEWER,
        member_id=current_user.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Update data
    update_data = jsonable_encoder(
        IndoorProjectUpdate(title="Should Not Update").model_dump()
    )

    # Attempt to update indoor project
    response = client.put(f"{API_URL}/{indoor_project.id}", json=update_data)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_indoor_project_as_non_member(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test that a non-member cannot update an indoor project.
    """
    # Create indoor project owned by someone else
    indoor_project = create_indoor_project(db)

    # Update data
    update_data = jsonable_encoder(
        IndoorProjectUpdate(title="Should Not Update").model_dump()
    )

    # Attempt to update indoor project
    response = client.put(f"{API_URL}/{indoor_project.id}", json=update_data)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_indoor_project_date_validation(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test date validation when updating an indoor project.
    """
    current_user = get_current_user(db, normal_user_access_token)

    # Valid - end_date after start_date
    indoor_project = create_indoor_project(
        db,
        owner_id=current_user.id,
        start_date=datetime(2024, 6, 1),
        end_date=None,
    )
    update_data = jsonable_encoder({"end_date": datetime(2024, 6, 2).isoformat()})
    response = client.put(f"{API_URL}/{indoor_project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK

    # Valid - start_date when no end_date set
    indoor_project = create_indoor_project(
        db, owner_id=current_user.id, start_date=None, end_date=None
    )
    update_data = jsonable_encoder({"start_date": datetime(2024, 6, 1).isoformat()})
    response = client.put(f"{API_URL}/{indoor_project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK

    # Invalid - end_date before start_date
    indoor_project = create_indoor_project(
        db,
        owner_id=current_user.id,
        start_date=datetime(2024, 6, 1),
        end_date=None,
    )
    update_data = jsonable_encoder({"end_date": datetime(2024, 5, 1).isoformat()})
    response = client.put(f"{API_URL}/{indoor_project.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Invalid - start_date after end_date
    indoor_project = create_indoor_project(
        db,
        owner_id=current_user.id,
        start_date=None,
        end_date=datetime(2024, 6, 1),
    )
    update_data = jsonable_encoder({"start_date": datetime(2024, 6, 2).isoformat()})
    response = client.put(f"{API_URL}/{indoor_project.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_deactivate_indoor_project_as_owner(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test deactivating an indoor project as owner.
    """
    # Create indoor project owned by current user
    current_user = get_current_user(db, normal_user_access_token)
    indoor_project = create_indoor_project(db, owner_id=current_user.id)

    # Deactivate indoor project
    response = client.delete(f"{API_URL}/{indoor_project.id}")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(indoor_project.id)

    # Verify it was deactivated
    deactivated_project = crud.indoor_project.get(db, id=indoor_project.id)
    assert deactivated_project is not None
    assert deactivated_project.is_active is False
    assert deactivated_project.deactivated_at is not None


def test_deactivate_indoor_project_as_manager(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test that a manager cannot deactivate an indoor project.
    """
    # Create indoor project owned by someone else
    indoor_project = create_indoor_project(db)

    # Add current user as manager
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db,
        role=Role.MANAGER,
        member_id=current_user.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Attempt to deactivate indoor project
    response = client.delete(f"{API_URL}/{indoor_project.id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_indoor_project_as_viewer(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test that a viewer cannot deactivate an indoor project.
    """
    # Create indoor project owned by someone else
    indoor_project = create_indoor_project(db)

    # Add current user as viewer
    current_user = get_current_user(db, normal_user_access_token)
    create_project_member(
        db,
        role=Role.VIEWER,
        member_id=current_user.id,
        project_uuid=indoor_project.id,
        project_type=ProjectType.INDOOR_PROJECT,
    )

    # Attempt to deactivate indoor project
    response = client.delete(f"{API_URL}/{indoor_project.id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_indoor_project_as_non_member(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test that a non-member cannot deactivate an indoor project.
    """
    # Create indoor project owned by someone else
    indoor_project = create_indoor_project(db)

    # Attempt to deactivate indoor project
    response = client.delete(f"{API_URL}/{indoor_project.id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_deactivated_indoor_project(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
    """
    Test that deactivated indoor projects cannot be accessed.
    """
    # Create and deactivate indoor project
    current_user = get_current_user(db, normal_user_access_token)
    indoor_project = create_indoor_project(db, owner_id=current_user.id)
    crud.indoor_project.deactivate(db, indoor_project_id=indoor_project.id)

    # Attempt to get deactivated indoor project
    response = client.get(f"{API_URL}/{indoor_project.id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
