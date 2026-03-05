import os
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.job import JobUpdate, Status
from app.schemas.role import Role
from app.tests.utils.job import create_job
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
        project_uuid=raw_data.project.id,
        role=Role.MANAGER,
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
        project_uuid=raw_data.project.id,
        role=Role.VIEWER,
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


def test_download_raw_data_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=raw_data.project.id,
        role=Role.VIEWER,
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}/download"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Type"] == "application/zip"

    with open(
        os.path.join(os.sep, "app", "app", "tests", "data", "test_raw_data.zip"), "rb"
    ) as test_data:
        assert len(test_data.read()) == len(response.content)


def test_download_raw_data_without_project_role(
    client: TestClient, db: Session
) -> None:
    raw_data = SampleRawData(db)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}/download"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


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
        project_uuid=project.id,
        role=Role.MANAGER,
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
        project_uuid=project.id,
        role=Role.VIEWER,
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
) -> None:
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
        deactivated_raw_data.get("deactivated_at"), "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    assert isinstance(deactivated_at, datetime)
    assert deactivated_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)


def test_deactivate_raw_data_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db)
    create_project_member(
        db,
        role=Role.MANAGER,
        member_id=current_user.id,
        project_uuid=raw_data.project.id,
    )
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_raw_data_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db)
    create_project_member(
        db,
        role=Role.VIEWER,
        member_id=current_user.id,
        project_uuid=raw_data.project.id,
    )
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_deactivate_raw_data_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def _patch_job_manager_db(db: Session):
    """Patch get_db in job_manager module so JobManager uses the test session."""
    return patch("app.utils.job_manager.get_db", return_value=iter([db]))


def test_progress_update_sets_progress_on_job(client: TestClient, db: Session) -> None:
    raw_data = SampleRawData(db)
    job = create_job(db, name="processing-raw-data", raw_data_id=raw_data.obj.id)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}/progress_update",
        json={"job_id": str(job.id), "progress": 42.5},
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["detail"] == "Progress updated"
    updated_job = crud.job.get(db, id=job.id)
    assert updated_job
    assert updated_job.extra["progress"] == 42.5


def test_progress_update_failure_signal_marks_job_failed(
    client: TestClient, db: Session
) -> None:
    raw_data = SampleRawData(db)
    job = create_job(db, name="processing-raw-data", raw_data_id=raw_data.obj.id)
    with _patch_job_manager_db(db):
        response = client.post(
            f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
            f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}/progress_update",
            json={"job_id": str(job.id), "progress": -9999},
        )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["detail"] == "Job marked as failed"
    updated_job = crud.job.get(db, id=job.id)
    assert updated_job
    assert updated_job.status == Status.FAILED


def test_progress_update_with_invalid_job_id(client: TestClient, db: Session) -> None:
    raw_data = SampleRawData(db)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}/progress_update",
        json={"job_id": str(uuid4()), "progress": 50.0},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_check_progress_returns_stored_progress(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db, user=current_user)
    job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        extra={"progress": 75.0},
    )
    with _patch_job_manager_db(db):
        response = client.get(
            f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
            f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
            f"/check_progress/{job.id}"
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["progress"] == "75.0"


def test_check_progress_returns_zero_when_no_progress(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db, user=current_user)
    job = create_job(db, name="processing-raw-data", raw_data_id=raw_data.obj.id)
    with _patch_job_manager_db(db):
        response = client.get(
            f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
            f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
            f"/check_progress/{job.id}"
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["progress"] == "0"


def test_check_progress_returns_error_when_job_failed(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db, user=current_user)
    job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        status=Status.FAILED,
    )
    with _patch_job_manager_db(db):
        response = client.get(
            f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
            f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
            f"/check_progress/{job.id}"
        )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_check_progress_with_invalid_job_id(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db, user=current_user)
    with _patch_job_manager_db(db):
        response = client.get(
            f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
            f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}"
            f"/check_progress/{uuid4()}"
        )
    assert response.status_code == status.HTTP_404_NOT_FOUND
