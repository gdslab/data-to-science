import os
import shutil
from datetime import datetime

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.file_permission import FilePermissionUpdate
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.flight import create_flight
from app.tests.utils.raw_data import SampleRawData
from app.tests.utils.user import create_user


def test_read_raw_data_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db, user=current_user)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_raw_data = response.json()
    assert str(raw_data.obj.id) == response_raw_data["id"]
    assert "flight_id" in response_raw_data
    assert "original_filename" in response_raw_data
    assert "status" in response_raw_data


def test_read_raw_data_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=raw_data.project.id,
        role="manager",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_raw_data = response.json()
    assert str(raw_data.obj.id) == response_raw_data["id"]


def test_read_raw_data_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=raw_data.project.id,
        role="viewer",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_raw_data = response.json()
    assert str(raw_data.obj.id) == response_raw_data["id"]


def test_read_raw_data_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_multi_raw_data_with_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleRawData(db, flight=flight, project=project, user=current_user)
    SampleRawData(db)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}" f"/flights/{flight.id}/raw_data"
    )
    assert response.status_code == status.HTTP_200_OK
    response_raw_data = response.json()
    assert type(response_raw_data) is list
    assert len(response_raw_data) == 3
    for dataset in response_raw_data:
        assert dataset["flight_id"] == str(flight.id)
        assert "original_filename" in dataset


def test_read_multi_raw_data_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleRawData(db, flight=flight, project=project, user=project_owner)
    SampleRawData(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=project.id,
        role="manager",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}" f"/flights/{flight.id}/raw_data"
    )
    assert response.status_code == status.HTTP_200_OK
    response_raw_data = response.json()
    assert type(response_raw_data) is list
    assert len(response_raw_data) == 3
    for dataset in response_raw_data:
        assert dataset["flight_id"] == str(flight.id)
        assert "original_filename" in dataset


def test_read_multi_raw_data_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleRawData(db, flight=flight, project=project, user=project_owner)
    SampleRawData(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=project.id,
        role="viewer",
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}" f"/flights/{flight.id}/raw_data"
    )
    assert response.status_code == status.HTTP_200_OK
    response_raw_data = response.json()
    assert type(response_raw_data) is list
    assert len(response_raw_data) == 3
    for dataset in response_raw_data:
        assert dataset["flight_id"] == str(flight.id)
        assert "original_filename" in dataset


def test_read_multi_raw_data_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    flight = create_flight(db, project_id=project.id)
    for i in range(0, 3):
        SampleRawData(
            db,
            flight=flight,
            project=project,
            user=project_owner,
        )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}" f"/flights/{flight.id}/raw_data"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_deactivate_raw_data_with_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
):
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db, user=current_user)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
    )
    assert response.status_code == status.HTTP_200_OK
    deactivated_raw_data = response.json()
    assert deactivated_raw_data
    assert deactivated_raw_data.get("id", None) == str(raw_data.obj.id)
    assert deactivated_raw_data.get("is_active", True) is False
    deactivated_at = datetime.strptime(
        deactivated_raw_data.get("deactivated_at"), "%Y-%m-%dT%H:%M:%S.%f"
    )
    assert isinstance(deactivated_at, datetime)
    assert deactivated_at < datetime.utcnow()


def test_deactivate_raw_data_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
):
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db)
    create_project_member(
        db, role="manager", member_id=current_user.id, project_id=raw_data.project.id
    )
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_raw_data_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
):
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db)
    create_project_member(
        db, role="viewer", member_id=current_user.id, project_id=raw_data.project.id
    )
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_raw_data_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
):
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
