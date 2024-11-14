import os
import tempfile
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app import crud
from app.schemas.indoor_project_data import (
    IndoorProjectDataCreate,
    IndoorProjectDataUpdate,
)
from app.tests.utils.indoor_project import create_indoor_project
from app.tests.utils.indoor_project_data import create_indoor_project_data
from app.tests.utils.user import create_user


def test_create_indoor_data(db: Session) -> None:
    """
    Test creating indoor data for an indoor project.
    """
    # create indoor project
    indoor_project = create_indoor_project(db)
    # user uploading the indoor data
    uploader = create_user(db)
    # create temporary "indoor data" file
    with tempfile.NamedTemporaryFile(suffix=".tar") as indoor_data_file:
        # required fields
        filename = os.path.basename(indoor_data_file.name)
        original_filenamme = "test_indoor_data"
        stored_filename = os.path.splitext(filename)[0]  # this will be random
        file_path = indoor_data_file.name
        file_size = os.stat(indoor_data_file.name).st_size
        file_type = os.path.splitext(original_filenamme)[1]
        upload_date = datetime.utcnow()
        # indoor data creation object
        indoor_data_in = IndoorProjectDataCreate(
            original_filename=original_filenamme,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            upload_date=upload_date,
        )
        # create indoor data in database
        indoor_data = crud.indoor_project_data.create_with_indoor_project(
            db,
            obj_in=indoor_data_in,
            indoor_project_id=indoor_project.id,
            uploader_id=uploader.id,
        )

        assert indoor_data.id
        assert indoor_data.original_filename == original_filenamme
        assert indoor_data.stored_filename == stored_filename
        assert indoor_data.file_path == file_path
        assert indoor_data.file_size == file_size
        assert indoor_data.file_type == file_type
        assert indoor_data.upload_date == upload_date
        assert indoor_data.uploader_id == uploader.id
        assert indoor_data.is_active is True
        assert indoor_data.deactivated_at is None


def test_read_indoor_data(db: Session) -> None:
    """
    Test reading indoor data from an indoor project.
    """
    # create indoor project data in db
    existing_indoor_project_data = create_indoor_project_data(db)

    # fetch indoor project data from db
    indoor_project_data_from_db = crud.indoor_project_data.read_by_id(
        db,
        indoor_project_id=existing_indoor_project_data.indoor_project_id,
        indoor_project_data_id=existing_indoor_project_data.id,
    )

    assert indoor_project_data_from_db
    assert indoor_project_data_from_db.id == existing_indoor_project_data.id
    assert (
        indoor_project_data_from_db.original_filename
        == existing_indoor_project_data.original_filename
    )
    assert (
        indoor_project_data_from_db.stored_filename
        == existing_indoor_project_data.stored_filename
    )
    assert (
        indoor_project_data_from_db.file_path == existing_indoor_project_data.file_path
    )
    assert (
        indoor_project_data_from_db.file_size == existing_indoor_project_data.file_size
    )
    assert (
        indoor_project_data_from_db.file_type == existing_indoor_project_data.file_type
    )
    assert (
        indoor_project_data_from_db.upload_date
        == existing_indoor_project_data.upload_date
    )
    assert (
        indoor_project_data_from_db.uploader_id
        == existing_indoor_project_data.uploader_id
    )
    assert (
        indoor_project_data_from_db.is_active == existing_indoor_project_data.is_active
    )
    assert (
        indoor_project_data_from_db.deactivated_at
        == existing_indoor_project_data.deactivated_at
    )


def test_read_multi_indoor_data(db: Session) -> None:
    """
    Test reading multiple indoor datasets from an indoor project.
    """
    # create indoor project
    indoor_project = create_indoor_project(db)

    # create two indoor project datasets in db
    existing_indoor_project_data1 = create_indoor_project_data(
        db, indoor_project_id=indoor_project.id
    )
    existing_indoor_project_data2 = create_indoor_project_data(
        db, indoor_project_id=indoor_project.id
    )

    # fetch indoor project datasets from db
    indoor_project_data_from_db = crud.indoor_project_data.read_multi_by_id(
        db, indoor_project_id=indoor_project.id
    )

    assert indoor_project_data_from_db
    assert isinstance(indoor_project_data_from_db, List)
    assert len(indoor_project_data_from_db) == 2
    for indoor_project_data in indoor_project_data_from_db:
        assert indoor_project_data.id in [
            existing_indoor_project_data1.id,
            existing_indoor_project_data2.id,
        ]


def test_update_indoor_data(db: Session) -> None:
    """
    Test updating indoor data from an indoor project.
    """
    # create indoor project data in db
    existing_indoor_project_data = create_indoor_project_data(db)

    # old original_filename
    old_original_filename = existing_indoor_project_data.original_filename

    # new values
    new_original_filename = "new_filename"

    assert old_original_filename != new_original_filename

    # indoor project update model
    indoor_project_data_update_in = IndoorProjectDataUpdate(
        original_filename=new_original_filename
    )

    # update record in database
    updated_indoor_project_data = crud.indoor_project_data.update(
        db, db_obj=existing_indoor_project_data, obj_in=indoor_project_data_update_in
    )

    assert updated_indoor_project_data
    assert updated_indoor_project_data.id == existing_indoor_project_data.id
    assert updated_indoor_project_data.original_filename == new_original_filename


def test_deactivate_indoor_data(db: Session) -> None:
    """
    Test deactivating indoor data from an indoor project.
    """
    # create indoor project data in db
    existing_indoor_project_data = create_indoor_project_data(db)

    # deactivate indoor project data in db
    deactivated_indoor_project_data = crud.indoor_project_data.deactivate(
        db,
        indoor_project_id=existing_indoor_project_data.indoor_project_id,
        indoor_project_data_id=existing_indoor_project_data.id,
    )

    assert deactivated_indoor_project_data
    assert deactivated_indoor_project_data.id == existing_indoor_project_data.id
    assert deactivated_indoor_project_data.is_active is False
    assert deactivated_indoor_project_data.deactivated_at
    assert deactivated_indoor_project_data.deactivated_at < datetime.utcnow()
