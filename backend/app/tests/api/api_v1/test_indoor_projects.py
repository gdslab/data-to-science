from datetime import datetime
from typing import List

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.indoor_project import create_indoor_project

API_URL = f"{settings.API_V1_STR}/indoor_projects"


def test_create_indoor_project(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
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


def test_read_indoor_projects(
    client: TestClient, normal_user_access_token: str, db: Session
) -> None:
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
