import pytest
from datetime import datetime

from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.schemas.file_permission import FilePermissionCreate, FilePermissionUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.raw_data import SampleRawData


def test_create_file_permission(db: Session) -> None:
    data_product = SampleDataProduct(db).obj
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.id
    )
    assert file_permission
    assert file_permission.is_public is False  # default
    assert (file_permission.expires_at - file_permission.created_at).days == 7
    assert file_permission.file_id == data_product.id


def test_create_duplicate_file_permission(db: Session) -> None:
    data_product = SampleDataProduct(db).obj  # creates file permission record
    with pytest.raises(IntegrityError):
        crud.file_permission.create_with_data_product(db, file_id=data_product.id)


def test_read_file_permission(db: Session) -> None:
    data_product = SampleDataProduct(db).obj
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.id
    )
    file_permission_in_db = crud.file_permission.get(db, id=file_permission.id)
    assert file_permission_in_db.id == file_permission.id
    assert file_permission_in_db.is_public == file_permission.is_public
    assert file_permission_in_db.created_at == file_permission.created_at
    assert file_permission_in_db.expires_at == file_permission.expires_at
    assert file_permission_in_db.file_id == file_permission.file_id


def test_read_file_permission_by_data_product_id(db: Session) -> None:
    data_product = SampleDataProduct(db).obj
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.id
    )
    file_permission_in_db = crud.file_permission.get_by_data_product(
        db, file_id=file_permission.file_id
    )
    assert file_permission_in_db.id == file_permission.id
    assert file_permission_in_db.is_public == file_permission.is_public
    assert file_permission_in_db.created_at == file_permission.created_at
    assert file_permission_in_db.expires_at == file_permission.expires_at
    assert file_permission_in_db.file_id == file_permission.file_id


def test_read_file_permission_by_filename(db: Session) -> None:
    data_product = SampleDataProduct(db).obj
    filename = data_product.filepath.split("flights")[1].split("/")[-1]
    file_permission = crud.file_permission.get_by_filename(db, filename=filename)
    assert file_permission
    assert file_permission.file_id == data_product.id


def test_update_file_permission(db: Session) -> None:
    data_product = SampleDataProduct(db).obj
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.id
    )
    file_permission_in_update = FilePermissionUpdate(is_public=True)
    file_permission_update = crud.file_permission.update(
        db, db_obj=file_permission, obj_in=file_permission_in_update
    )
    assert file_permission.id == file_permission_update.id
    assert file_permission_update.is_public is True


def test_delete_file_permission(db: Session) -> None:
    data_product = SampleDataProduct(db).obj
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.id
    )
    file_permission2 = crud.file_permission.remove(db, id=file_permission.id)
    file_permission3 = crud.file_permission.get(db, id=file_permission.id)
    assert file_permission3 is None
    assert file_permission2
    assert file_permission2.id == file_permission.id
    assert file_permission2.is_public == file_permission.is_public
    assert file_permission2.file_id == file_permission.file_id


# Tests for RawData FilePermission functionality


def test_create_file_permission_with_raw_data(db: Session) -> None:
    """Test creating FilePermission for RawData."""
    raw_data = SampleRawData(db).obj
    file_permission = crud.file_permission.get_by_raw_data(db, raw_data_id=raw_data.id)

    assert file_permission
    assert file_permission.is_public is False  # default
    assert file_permission.raw_data_id == raw_data.id
    assert file_permission.file_id is None
    assert (file_permission.expires_at - file_permission.created_at).days == 7


def test_create_duplicate_raw_data_permission(db: Session) -> None:
    """Test unique constraint on raw_data_id."""
    raw_data = SampleRawData(db).obj  # creates file permission record
    with pytest.raises(IntegrityError):
        crud.file_permission.create_with_raw_data(db, raw_data_id=raw_data.id)


def test_get_file_permission_by_raw_data(db: Session) -> None:
    """Test retrieving FilePermission by RawData ID."""
    raw_data = SampleRawData(db).obj
    file_permission = crud.file_permission.get_by_raw_data(db, raw_data_id=raw_data.id)

    assert file_permission
    assert file_permission.raw_data_id == raw_data.id
    assert file_permission.file_id is None

    # Verify it's the same record when fetched again
    file_permission_in_db = crud.file_permission.get(db, id=file_permission.id)
    assert file_permission_in_db.id == file_permission.id
    assert file_permission_in_db.raw_data_id == raw_data.id


def test_update_raw_data_file_permission(db: Session) -> None:
    """Test updating FilePermission for RawData."""
    raw_data = SampleRawData(db).obj
    file_permission = crud.file_permission.get_by_raw_data(db, raw_data_id=raw_data.id)

    # Update to public
    file_permission_in_update = FilePermissionUpdate(is_public=True)
    file_permission_update = crud.file_permission.update(
        db, db_obj=file_permission, obj_in=file_permission_in_update
    )

    assert file_permission.id == file_permission_update.id
    assert file_permission_update.is_public is True
    assert file_permission_update.raw_data_id == raw_data.id


def test_update_project_visibility_updates_raw_data_permissions(db: Session) -> None:
    """Test that update_project_visibility() updates RawData FilePermissions."""
    # Create a project with both DataProduct and RawData
    data_product = SampleDataProduct(db).obj

    # Query flight and project fresh from database to avoid DetachedInstanceError
    flight = crud.flight.get(db, id=data_product.flight_id)
    project = crud.project.get(db, id=flight.project_id)

    # Create RawData with the fresh flight and project objects
    raw_data = SampleRawData(db, project=project, flight=flight).obj

    # Verify both FilePermissions start as private
    dp_file_permission = crud.file_permission.get_by_data_product(db, file_id=data_product.id)
    raw_file_permission = crud.file_permission.get_by_raw_data(db, raw_data_id=raw_data.id)
    assert dp_file_permission.is_public is False
    assert raw_file_permission.is_public is False

    # Publish the project (make public)
    crud.project.update_project_visibility(
        db, project_id=project.id, is_public=True
    )

    # Verify both FilePermissions are now public
    dp_file_permission = crud.file_permission.get_by_data_product(db, file_id=data_product.id)
    raw_file_permission = crud.file_permission.get_by_raw_data(db, raw_data_id=raw_data.id)
    assert dp_file_permission.is_public is True
    assert raw_file_permission.is_public is True

    # Verify project is published
    project = crud.project.get(db, id=project.id)
    assert project.is_published is True

    # Unpublish the project (make private)
    crud.project.update_project_visibility(
        db, project_id=project.id, is_public=False
    )

    # Verify both FilePermissions are now private again
    dp_file_permission = crud.file_permission.get_by_data_product(db, file_id=data_product.id)
    raw_file_permission = crud.file_permission.get_by_raw_data(db, raw_data_id=raw_data.id)
    assert dp_file_permission.is_public is False
    assert raw_file_permission.is_public is False

    # Verify project is unpublished
    project = crud.project.get(db, id=project.id)
    assert project.is_published is False
