import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.api_v1.endpoints.raw_data import has_active_processing_job
from app.api.deps import get_current_user
from app.crud.crud_raw_data import set_report_attr
from app.core.config import settings
from app.schemas.job import JobUpdate, State, Status
from app.tasks.raw_image_processing_tasks import (
    start_raw_data_processing,
    transfer_raw_data,
)
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


def test_read_raw_data_jobs(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db, user=current_user)
    odm_settings = {"orthoResolution": 4.0, "pcQuality": "medium"}
    older_job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        start_time=datetime.now(tz=timezone.utc) - timedelta(hours=1),
    )
    newer_job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        start_time=datetime.now(tz=timezone.utc),
        extra={"backend": "odm", "settings": odm_settings},
    )
    create_job(db, name="upload-raw-data", raw_data_id=raw_data.obj.id)

    url = (
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}/jobs"
    )

    # all jobs for raw data
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    response_job_names = [job["name"] for job in response.json()]
    assert "upload-raw-data" in response_job_names
    assert response_job_names.count("processing-raw-data") == 2

    # filtered by job name and ordered newest first
    response = client.get(url, params={"name": "processing-raw-data"})
    assert response.status_code == status.HTTP_200_OK
    response_jobs = response.json()
    assert len(response_jobs) == 2
    assert response_jobs[0]["id"] == str(newer_job.id)
    assert response_jobs[0]["extra"] == {"backend": "odm", "settings": odm_settings}
    assert response_jobs[1]["id"] == str(older_job.id)
    assert response_jobs[1]["extra"] is None


def test_read_raw_data_jobs_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    raw_data = SampleRawData(db)
    create_job(db, name="processing-raw-data", raw_data_id=raw_data.obj.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}/jobs"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_raw_data_jobs_with_raw_data_from_other_flight(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    raw_data = SampleRawData(db, user=current_user)
    other_raw_data = SampleRawData(db, user=current_user)
    create_job(
        db, name="processing-raw-data", raw_data_id=other_raw_data.obj.id
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{other_raw_data.obj.id}/jobs"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_start_raw_data_processing_preserves_settings_in_extra(
    client: TestClient, db: Session
) -> None:
    raw_data = SampleRawData(db)
    job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        extra={
            "backend": "odm",
            "settings": {"orthoResolution": 4.0, "pcQuality": "medium"},
        },
    )
    mock_rpc_client = MagicMock()
    mock_rpc_client.return_value.__enter__.return_value.call.return_value = "batch123"
    with _patch_job_manager_db(db), patch(
        "app.tasks.raw_image_processing_tasks.RpcClient", mock_rpc_client
    ):
        start_raw_data_processing((job.id, "raw-data-identifier"))
    updated_job = crud.job.get(db, id=job.id)
    assert updated_job
    assert updated_job.status == Status.INPROGRESS
    assert updated_job.extra == {
        "backend": "odm",
        "settings": {"orthoResolution": 4.0, "pcQuality": "medium"},
        "batch_id": "batch123",
    }


ODM_EXTRA = {
    "backend": "odm",
    "settings": {"orthoResolution": 4.0, "pcQuality": "medium"},
}


def _transfer_task_args(raw_data: SampleRawData, job_id, external_storage_dir: str):
    return (
        external_storage_dir,
        raw_data.obj.filepath,
        raw_data.obj.original_filename,
        "test_project",
        raw_data.project.id,
        raw_data.flight.id,
        raw_data.obj.id,
        raw_data.user.id,
        job_id,
        "odm",
        dict(ODM_EXTRA["settings"]),
    )


def _patch_task_db(db: Session):
    """Patch get_db in the raw image processing task module."""
    return patch(
        "app.tasks.raw_image_processing_tasks.get_db",
        side_effect=lambda: iter([db]),
    )


def test_transfer_raw_data_marks_job_failed_when_storage_inaccessible(
    client: TestClient, db: Session, tmp_path
) -> None:
    raw_data = SampleRawData(db)
    job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        extra=dict(ODM_EXTRA),
    )
    with _patch_job_manager_db(db), _patch_task_db(db), patch(
        "app.tasks.raw_image_processing_tasks.os.makedirs",
        side_effect=PermissionError(13, "Permission denied"),
    ):
        result = transfer_raw_data.apply(
            args=_transfer_task_args(raw_data, job.id, str(tmp_path))
        )
    assert result.failed()
    updated_job = crud.job.get(db, id=job.id)
    assert updated_job
    assert updated_job.status == Status.FAILED
    assert updated_job.state == State.COMPLETED
    assert updated_job.extra["settings"] == ODM_EXTRA["settings"]
    assert "detail" in updated_job.extra


def test_transfer_raw_data_metadata_failure_aborts_chain(
    client: TestClient, db: Session, tmp_path
) -> None:
    raw_data = SampleRawData(db)
    job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        extra=dict(ODM_EXTRA),
    )
    mock_cleanup = MagicMock()
    with _patch_job_manager_db(db), _patch_task_db(db), patch(
        "app.tasks.raw_image_processing_tasks.async_transfer", new=MagicMock()
    ), patch(
        "app.tasks.raw_image_processing_tasks.asyncio.run", new=MagicMock()
    ), patch(
        "app.tasks.raw_image_processing_tasks.get_token_hash",
        side_effect=Exception("token error"),
    ), patch(
        "app.tasks.raw_image_processing_tasks.cleanup_on_external", mock_cleanup
    ):
        result = transfer_raw_data.apply(
            args=_transfer_task_args(raw_data, job.id, str(tmp_path))
        )
    assert result.failed()
    mock_cleanup.assert_called_once()
    updated_job = crud.job.get(db, id=job.id)
    assert updated_job
    assert updated_job.status == Status.FAILED
    assert updated_job.extra["settings"] == ODM_EXTRA["settings"]
    assert "detail" in updated_job.extra


def test_start_raw_data_processing_marks_job_failed_on_rpc_error(
    client: TestClient, db: Session
) -> None:
    raw_data = SampleRawData(db)
    job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        extra=dict(ODM_EXTRA),
    )
    mock_rpc_client = MagicMock()
    mock_rpc_client.return_value.__enter__.return_value.call.side_effect = Exception(
        "rpc unavailable"
    )
    with _patch_job_manager_db(db), patch(
        "app.tasks.raw_image_processing_tasks.RpcClient", mock_rpc_client
    ):
        start_raw_data_processing((job.id, "raw-data-identifier"))
    updated_job = crud.job.get(db, id=job.id)
    assert updated_job
    assert updated_job.status == Status.FAILED
    assert updated_job.extra["settings"] == ODM_EXTRA["settings"]
    assert "detail" in updated_job.extra


def test_start_raw_data_processing_continues_without_batch_id(
    client: TestClient, db: Session
) -> None:
    raw_data = SampleRawData(db)
    job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        status=Status.INPROGRESS,
        extra=dict(ODM_EXTRA),
    )
    mock_rpc_client = MagicMock()
    mock_rpc_client.return_value.__enter__.return_value.call.return_value = ""
    with _patch_job_manager_db(db), patch(
        "app.tasks.raw_image_processing_tasks.RpcClient", mock_rpc_client
    ):
        start_raw_data_processing((job.id, "raw-data-identifier"))
    updated_job = crud.job.get(db, id=job.id)
    assert updated_job
    assert updated_job.status == Status.INPROGRESS
    assert updated_job.extra == ODM_EXTRA


def test_start_raw_data_processing_fails_on_error_reply(
    client: TestClient, db: Session
) -> None:
    raw_data = SampleRawData(db)
    job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        extra=dict(ODM_EXTRA),
    )
    mock_rpc_client = MagicMock()
    mock_rpc_client.return_value.__enter__.return_value.call.return_value = (
        "Error: unable to create project"
    )
    with _patch_job_manager_db(db), patch(
        "app.tasks.raw_image_processing_tasks.RpcClient", mock_rpc_client
    ):
        start_raw_data_processing((job.id, "raw-data-identifier"))
    updated_job = crud.job.get(db, id=job.id)
    assert updated_job
    assert updated_job.status == Status.FAILED
    assert updated_job.extra["settings"] == ODM_EXTRA["settings"]
    assert "detail" in updated_job.extra


def test_has_active_processing_job_marks_stale_job_failed(
    client: TestClient, db: Session
) -> None:
    raw_data = SampleRawData(db)
    stale_job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        status=Status.INPROGRESS,
        start_time=datetime.now(tz=timezone.utc) - timedelta(hours=25),
        extra=dict(ODM_EXTRA),
    )
    with _patch_job_manager_db(db):
        assert has_active_processing_job(db, raw_data.obj.id) is False
    updated_job = crud.job.get(db, id=stale_job.id)
    assert updated_job
    assert updated_job.status == Status.FAILED
    assert updated_job.state == State.COMPLETED
    assert "detail" in updated_job.extra

    # a fresh unfinished job counts as active and is left untouched
    fresh_job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        status=Status.INPROGRESS,
        start_time=datetime.now(tz=timezone.utc) - timedelta(hours=1),
    )
    with _patch_job_manager_db(db):
        assert has_active_processing_job(db, raw_data.obj.id) is True
    updated_fresh_job = crud.job.get(db, id=fresh_job.id)
    assert updated_fresh_job
    assert updated_fresh_job.status == Status.INPROGRESS


def test_progress_update_stores_batch_id_when_provided(
    client: TestClient, db: Session
) -> None:
    raw_data = SampleRawData(db)
    job = create_job(
        db,
        name="processing-raw-data",
        raw_data_id=raw_data.obj.id,
        extra=dict(ODM_EXTRA),
    )
    response = client.post(
        f"{settings.API_V1_STR}/projects/{raw_data.project.id}"
        f"/flights/{raw_data.flight.id}/raw_data/{raw_data.obj.id}/progress_update",
        json={"job_id": str(job.id), "progress": 12.5, "batch_id": "batch987"},
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    updated_job = crud.job.get(db, id=job.id)
    assert updated_job
    assert updated_job.extra["progress"] == 12.5
    assert updated_job.extra["batch_id"] == "batch987"
    assert updated_job.extra["settings"] == ODM_EXTRA["settings"]


def test_set_report_attr_prefers_newest_report(
    client: TestClient, db: Session
) -> None:
    raw_data = SampleRawData(db)
    raw_data_dir = Path(raw_data.obj.filepath).parent
    now = time.time()

    legacy_report = raw_data_dir / "report.pdf"
    legacy_report.write_bytes(b"legacy report")
    os.utime(legacy_report, (now - 100, now - 100))

    per_job_report = raw_data_dir / f"report_{uuid4()}.pdf"
    per_job_report.write_bytes(b"newer report")
    os.utime(per_job_report, (now, now))

    set_report_attr(raw_data.obj)
    assert raw_data.obj.report.endswith(per_job_report.name)

    # with only the legacy report present, it is still picked up
    per_job_report.unlink()
    set_report_attr(raw_data.obj)
    assert raw_data.obj.report.endswith("report.pdf")
