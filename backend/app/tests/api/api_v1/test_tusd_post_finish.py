from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.tusd import MAX_ORIGINAL_FILENAME_BYTES, MetaData
from app.tests.utils.flight import create_flight
from app.tests.utils.indoor_project import create_indoor_project
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user, login_and_get_access_token


def _build_tusd_post_finish_payload(
    *,
    upload_id: str,
    storage_path: str,
    cookie: list[str],
    project_id: str | None = None,
    flight_id: str | None = None,
    data_type: str | None = None,
    indoor_project_id: str | None = None,
    treatment: str | None = None,
) -> dict:
    """Build a minimal tusd post-finish hook payload."""
    return {
        "Type": "post-finish",
        "Event": {
            "Upload": {
                "ID": upload_id,
                "Size": 1024,
                "SizeIsDeferred": False,
                "Offset": 1024,
                "MetaData": {
                    "filename": "test.tif",
                    "filetype": "image/tiff",
                    "name": "test.tif",
                    "relativePath": "null",
                    "type": "image/tiff",
                },
                "IsPartial": False,
                "IsFinal": False,
                "PartialUploads": None,
                "Storage": {"Path": storage_path, "Type": "filestore"},
            },
            "HTTPRequest": {
                "Method": "PATCH",
                "URI": "/files/",
                "RemoteAddr": "127.0.0.1",
                "Header": {
                    "Accept": ["*/*"],
                    "Accept-Encoding": ["gzip"],
                    "Accept-Language": ["en-US"],
                    "Connection": ["keep-alive"],
                    "Cookie": cookie,
                    "Host": ["localhost"],
                    "Origin": ["http://localhost"],
                    "Tus-Resumable": ["1.0.0"],
                    "User-Agent": ["test"],
                    "X-Forwarded-Host": ["localhost"],
                    "X-Forwarded-Proto": ["http"],
                    **({"X-Project-Id": [project_id]} if project_id else {}),
                    **({"X-Flight-Id": [flight_id]} if flight_id else {}),
                    **({"X-Data-Type": [data_type]} if data_type else {}),
                    **(
                        {"X-Indoor-Project-Id": [indoor_project_id]}
                        if indoor_project_id
                        else {}
                    ),
                    **({"X-Treatment": [treatment]} if treatment else {}),
                },
            },
        },
    }


@pytest.fixture
def process_data_product_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Capture calls to the UAS data product post-processing function."""
    calls: list[dict] = []

    def fake_process(db: Session, **kwargs) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(
        "app.api.api_v1.endpoints.tusd.process_data_product_uploaded_to_tusd",
        fake_process,
    )
    return calls


@pytest.fixture
def process_indoor_data_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Capture calls to the indoor data post-processing function."""
    calls: list[dict] = []

    def fake_process(db: Session, **kwargs) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(
        "app.api.api_v1.endpoints.tusd.process_indoor_data_uploaded_to_tusd",
        fake_process,
    )
    return calls


def _create_uploaded_file(tmp_path: Path) -> str:
    """Create a dummy uploaded file in tusd storage and return its path."""
    uploaded_file = tmp_path / uuid4().hex
    uploaded_file.write_bytes(b"fake geotiff bytes")
    return str(uploaded_file)


def test_post_finish_without_upload_record_creates_record_and_processes(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    process_data_product_calls: list[dict],
    tmp_path: Path,
) -> None:
    """Post-finish arriving before post-create recorded the upload (hook race)
    should create the record from the forwarded cookie and still process."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    upload_id = uuid4().hex

    payload = _build_tusd_post_finish_payload(
        upload_id=upload_id,
        storage_path=_create_uploaded_file(tmp_path),
        cookie=[f"access_token=Bearer {normal_user_access_token}"],
        project_id=str(project.id),
        flight_id=str(flight.id),
        data_type="dsm",
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    upload_record = crud.upload.get_upload_by_upload_id(db, upload_id=upload_id)
    assert upload_record is not None
    assert upload_record.is_uploading is False
    assert upload_record.user_id == current_user.id
    assert len(process_data_product_calls) == 1
    call = process_data_product_calls[0]
    assert call["user_id"] == current_user.id
    assert call["project_id"] == project.id
    assert call["flight_id"] == flight.id
    assert call["dtype"] == "dsm"


def test_post_finish_without_upload_record_and_missing_token_returns_error(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    process_data_product_calls: list[dict],
    tmp_path: Path,
) -> None:
    """Post-finish with no upload record and no access token cannot resolve a
    user for ownership and must fail without processing."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    upload_id = uuid4().hex

    payload = _build_tusd_post_finish_payload(
        upload_id=upload_id,
        storage_path=_create_uploaded_file(tmp_path),
        cookie=[],
        project_id=str(project.id),
        flight_id=str(flight.id),
        data_type="dsm",
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert crud.upload.get_upload_by_upload_id(db, upload_id=upload_id) is None
    assert len(process_data_product_calls) == 0


def test_post_finish_without_upload_record_and_invalid_token_returns_error(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    process_data_product_calls: list[dict],
    tmp_path: Path,
) -> None:
    """Post-finish with no upload record and an invalid token must fail
    without creating a record or processing."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    upload_id = uuid4().hex

    payload = _build_tusd_post_finish_payload(
        upload_id=upload_id,
        storage_path=_create_uploaded_file(tmp_path),
        cookie=["access_token=Bearer not-a-valid-jwt"],
        project_id=str(project.id),
        flight_id=str(flight.id),
        data_type="dsm",
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert crud.upload.get_upload_by_upload_id(db, upload_id=upload_id) is None
    assert len(process_data_product_calls) == 0


def test_post_finish_created_record_requires_project_permission(
    client: TestClient,
    db: Session,
    process_data_product_calls: list[dict],
    tmp_path: Path,
) -> None:
    """When post-finish creates the missing record, the resolved user must
    still have read/write access to the project."""
    password = "SecurePassword123"
    other_user = create_user(db, password=password)
    other_token = login_and_get_access_token(
        client=client, email=other_user.email, password=password
    )
    project = create_project(db)  # owned by a different random user
    flight = create_flight(db, project_id=project.id)
    upload_id = uuid4().hex

    payload = _build_tusd_post_finish_payload(
        upload_id=upload_id,
        storage_path=_create_uploaded_file(tmp_path),
        cookie=[f"access_token=Bearer {other_token}"],
        project_id=str(project.id),
        flight_id=str(flight.id),
        data_type="dsm",
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert len(process_data_product_calls) == 0


def test_post_finish_with_in_progress_upload_record_processes(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    process_data_product_calls: list[dict],
    tmp_path: Path,
) -> None:
    """Post-finish with an in-progress upload record (normal hook order)
    marks it finished and runs post-processing."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    upload_id = uuid4().hex
    crud.upload.create_with_user(
        db, upload_id=upload_id, user_id=current_user.id, is_uploading=True
    )

    payload = _build_tusd_post_finish_payload(
        upload_id=upload_id,
        storage_path=_create_uploaded_file(tmp_path),
        cookie=[f"access_token=Bearer {normal_user_access_token}"],
        project_id=str(project.id),
        flight_id=str(flight.id),
        data_type="dsm",
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    upload_record = crud.upload.get_upload_by_upload_id(db, upload_id=upload_id)
    assert upload_record is not None
    assert upload_record.is_uploading is False
    assert len(process_data_product_calls) == 1


def test_post_finish_with_existing_record_does_not_require_token(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    process_data_product_calls: list[dict],
    tmp_path: Path,
) -> None:
    """Post-finish with an existing upload record must not depend on the
    cookie (e.g., token expired mid-upload)."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    upload_id = uuid4().hex
    crud.upload.create_with_user(
        db, upload_id=upload_id, user_id=current_user.id, is_uploading=True
    )

    payload = _build_tusd_post_finish_payload(
        upload_id=upload_id,
        storage_path=_create_uploaded_file(tmp_path),
        cookie=[],
        project_id=str(project.id),
        flight_id=str(flight.id),
        data_type="dsm",
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert len(process_data_product_calls) == 1


def test_post_finish_with_finished_upload_record_skips_processing(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    process_data_product_calls: list[dict],
    tmp_path: Path,
) -> None:
    """Post-finish for an upload already marked finished (replayed hook) must
    not process the file again."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    upload_id = uuid4().hex
    crud.upload.create_with_user(
        db, upload_id=upload_id, user_id=current_user.id, is_uploading=False
    )

    payload = _build_tusd_post_finish_payload(
        upload_id=upload_id,
        storage_path=_create_uploaded_file(tmp_path),
        cookie=[f"access_token=Bearer {normal_user_access_token}"],
        project_id=str(project.id),
        flight_id=str(flight.id),
        data_type="dsm",
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert len(process_data_product_calls) == 0


def test_post_finish_indoor_without_upload_record_creates_record_and_processes(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    process_indoor_data_calls: list[dict],
    tmp_path: Path,
) -> None:
    """Indoor post-finish with a missing upload record should create it from
    the forwarded cookie and still process."""
    current_user = get_current_user(db, normal_user_access_token)
    indoor_project = create_indoor_project(db, owner_id=current_user.id)
    upload_id = uuid4().hex

    payload = _build_tusd_post_finish_payload(
        upload_id=upload_id,
        storage_path=_create_uploaded_file(tmp_path),
        cookie=[f"access_token=Bearer {normal_user_access_token}"],
        indoor_project_id=str(indoor_project.id),
        treatment="control",
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    upload_record = crud.upload.get_upload_by_upload_id(db, upload_id=upload_id)
    assert upload_record is not None
    assert upload_record.is_uploading is False
    assert upload_record.user_id == current_user.id
    assert len(process_indoor_data_calls) == 1
    call = process_indoor_data_calls[0]
    assert call["user_id"] == current_user.id
    assert call["indoor_project_id"] == indoor_project.id
    assert call["treatment"] == "control"


def test_post_finish_indoor_created_record_requires_project_permission(
    client: TestClient,
    db: Session,
    process_indoor_data_calls: list[dict],
    tmp_path: Path,
) -> None:
    """Indoor post-finish resolving a user without access to the indoor
    project must fail without processing."""
    password = "SecurePassword123"
    other_user = create_user(db, password=password)
    other_token = login_and_get_access_token(
        client=client, email=other_user.email, password=password
    )
    indoor_project = create_indoor_project(db)  # owned by a different random user
    upload_id = uuid4().hex

    payload = _build_tusd_post_finish_payload(
        upload_id=upload_id,
        storage_path=_create_uploaded_file(tmp_path),
        cookie=[f"access_token=Bearer {other_token}"],
        indoor_project_id=str(indoor_project.id),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert len(process_indoor_data_calls) == 0


def test_metadata_strips_control_characters_from_the_filename() -> None:
    """Non-printable characters are removed before the name is stored."""
    metadata = MetaData(
        filename="  ortho\n\t\x00.tif  ",
        filetype="image/tiff",
        name="ortho.tif",
        relativePath="null",
        type="image/tiff",
    )

    assert metadata.filename == "ortho.tif"


def test_metadata_truncates_a_long_filename_instead_of_rejecting_it() -> None:
    """An over-long name is bounded, not refused.

    This model validates the whole tusd hook payload, so rejecting would fail the
    hook itself: at pre-create the upload is refused with an opaque error, and at
    post-finish the bytes are already on the tus server while no data product
    record is ever created.
    """
    metadata = MetaData(
        filename=f"{'a' * 400}.tif",
        filetype="image/tiff",
        name="ortho.tif",
        relativePath="null",
        type="image/tiff",
    )

    assert len(metadata.filename.encode("utf-8")) == MAX_ORIGINAL_FILENAME_BYTES


def test_metadata_trims_before_applying_the_length_cap() -> None:
    """Trimming runs first, so padding cannot push a valid name over the cap.

    Running the cap first would reject a name that fits once its control
    characters are gone.
    """
    padded = f"{'a' * 250}.tif" + "\x00" * 100

    metadata = MetaData(
        filename=padded,
        filetype="image/tiff",
        name="ortho.tif",
        relativePath="null",
        type="image/tiff",
    )

    assert metadata.filename == f"{'a' * 250}.tif"


def test_post_finish_accepts_an_upload_with_a_long_filename(
    client: TestClient, db: Session
) -> None:
    """A long file name does not fail the hook.

    The name is only provenance, so bounding what gets stored is the goal rather
    than gatekeeping the upload.
    """
    password = "SecurePassword123"
    user = create_user(db, password=password)
    token = login_and_get_access_token(
        client=client, email=user.email, password=password
    )
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=user.id)

    payload = _build_tusd_post_finish_payload(
        upload_id=uuid4().hex,
        storage_path="/does/not/exist.tif",
        cookie=[f"access_token={token}"],
        project_id=str(project.id),
        flight_id=str(flight.id),
        data_type="dsm",
    )
    payload["Event"]["Upload"]["MetaData"]["filename"] = f"{'a' * 400}.tif"

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    # anything other than 422 shows the payload itself validated
    assert response.status_code != status.HTTP_422_UNPROCESSABLE_CONTENT
