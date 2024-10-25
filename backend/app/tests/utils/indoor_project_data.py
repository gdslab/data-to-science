import os
import tempfile
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app import crud
from app.models.indoor_project_data import IndoorProjectData
from app.schemas.indoor_project_data import IndoorProjectDataCreate
from app.tests.utils.indoor_project import create_indoor_project
from app.tests.utils.user import create_user


def create_indoor_project_data(
    db: Session,
    indoor_project_id: Optional[UUID] = None,
    uploader_id: Optional[UUID] = None,
) -> IndoorProjectData:
    """
    Creates indoor project data.
    """
    if indoor_project_id is None:
        indoor_project = create_indoor_project(db)
        indoor_project_id = indoor_project.id
    if uploader_id is None:
        uploader = create_user(db)
        uploader_id = uploader.id

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
            indoor_project_id=indoor_project_id,
            uploader_id=uploader.id,
        )

        return indoor_data
