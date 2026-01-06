import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.tests.utils.flight import create_flight
from app.tests.utils.raw_data import SampleRawData
from app.tests.utils.user import create_user


def test_create_raw_data(db: Session) -> None:
    raw_data = SampleRawData(db)
    assert raw_data.obj
    assert raw_data.obj.original_filename == "myrawdata.zip"
    assert raw_data.obj.is_initial_processing_completed is True
    assert os.path.exists(raw_data.obj.filepath)
    assert raw_data.obj.created_at is not None
    assert raw_data.obj.updated_at is not None
    assert raw_data.obj.updated_at >= raw_data.obj.created_at


def test_read_raw_data(db: Session) -> None:
    raw_data = SampleRawData(db)
    stored_raw_data = crud.raw_data.get_single_by_id(
        db,
        raw_data_id=raw_data.obj.id,
        upload_dir=settings.TEST_STATIC_DIR,
    )
    assert stored_raw_data
    assert stored_raw_data.id == raw_data.obj.id
    assert stored_raw_data.flight_id == raw_data.flight.id
    assert stored_raw_data.filepath == raw_data.obj.filepath
    assert stored_raw_data.original_filename == raw_data.obj.original_filename
    assert (
        stored_raw_data.is_initial_processing_completed
        == raw_data.obj.is_initial_processing_completed
    )
    assert stored_raw_data.created_at is not None
    assert stored_raw_data.updated_at is not None


def test_read_multi_raw_data(db: Session) -> None:
    user = create_user(db)
    flight = create_flight(db)
    SampleRawData(db, flight=flight, user=user)
    SampleRawData(db, flight=flight, user=user)
    SampleRawData(db, flight=flight, user=user)
    SampleRawData(db)
    raw_data = crud.raw_data.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=settings.TEST_STATIC_DIR
    )
    assert type(raw_data) is list
    assert len(raw_data) == 3
    for dataset in raw_data:
        assert dataset.flight_id == flight.id


def test_deactivate_raw_data(db: Session) -> None:
    user = create_user(db)
    raw_data = SampleRawData(db, user=user)
    raw_data2 = crud.raw_data.deactivate(db, raw_data_id=raw_data.obj.id)
    raw_data3 = crud.raw_data.get(db, id=raw_data.obj.id)
    assert raw_data2 and raw_data3
    assert raw_data3.id == raw_data.obj.id
    assert raw_data3.is_active is False
    assert isinstance(raw_data3.deactivated_at, datetime)
    assert raw_data3.deactivated_at.replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    )


def test_read_raw_data_url_attribute(db: Session) -> None:
    """Test that url attribute is set on raw_data objects."""
    raw_data = SampleRawData(db)
    stored_raw_data = crud.raw_data.get_single_by_id(
        db,
        raw_data_id=raw_data.obj.id,
        upload_dir=settings.TEST_STATIC_DIR,
    )
    assert stored_raw_data
    # Verify url attribute exists and is set correctly
    assert hasattr(stored_raw_data, "url")
    assert stored_raw_data.url is not None
    assert isinstance(stored_raw_data.url, str)
    assert settings.STATIC_DIR in stored_raw_data.url


def test_read_multi_raw_data_url_attribute(db: Session) -> None:
    """Test that url attribute is set on all raw_data objects from get_multi_by_flight."""
    user = create_user(db)
    flight = create_flight(db)
    SampleRawData(db, flight=flight, user=user)
    SampleRawData(db, flight=flight, user=user)
    raw_data_list = crud.raw_data.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=settings.TEST_STATIC_DIR
    )
    assert len(raw_data_list) == 2
    # Verify all objects have url attribute
    for raw_data in raw_data_list:
        assert hasattr(raw_data, "url")
        assert raw_data.url is not None
        assert isinstance(raw_data.url, str)
        assert settings.STATIC_DIR in raw_data.url


def test_read_raw_data_url_attribute_with_invalid_upload_dir(db: Session) -> None:
    """Test that url attribute is set to None when upload_dir doesn't match filepath."""
    raw_data = SampleRawData(db)
    # Use an invalid upload_dir that doesn't match the filepath
    invalid_upload_dir = "/invalid/path"
    stored_raw_data = crud.raw_data.get_single_by_id(
        db,
        raw_data_id=raw_data.obj.id,
        upload_dir=invalid_upload_dir,
    )
    assert stored_raw_data
    # Verify url attribute exists but is None due to ValueError
    assert hasattr(stored_raw_data, "url")
    assert stored_raw_data.url is None


def test_create_raw_data_creates_file_permission(db: Session) -> None:
    """Test that creating RawData automatically creates FilePermission."""
    raw_data = SampleRawData(db).obj

    # Verify FilePermission was created
    file_permission = crud.file_permission.get_by_raw_data(db, raw_data_id=raw_data.id)
    assert file_permission
    assert file_permission.raw_data_id == raw_data.id
    assert file_permission.file_id is None
    assert file_permission.is_public is False  # Should default to private
