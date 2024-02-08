import logging
import os
import shutil
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
    UploadFile,
)
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()


logger = logging.getLogger("__name__")


def get_raw_data_dir(project_id: str, flight_id: str, raw_data_id: str) -> str:
    """Construct path to directory that will store uploaded raw data.

    Args:
        project_id (str): Project ID associated with raw data.
        flight_id (str): Flight ID associated with raw data.
        raw_data_id (str): ID for raw data.

    Returns:
        str: Full path to raw data directory.
    """
    # get root static path
    if os.environ.get("RUNNING_TESTS") == "1":
        raw_data_dir = Path(settings.TEST_STATIC_DIR)
    else:
        raw_data_dir = Path(settings.STATIC_DIR)
    # construct path to project/flight/rawdata
    raw_data_dir = raw_data_dir / "projects" / project_id
    raw_data_dir = raw_data_dir / "flights" / flight_id
    raw_data_dir = raw_data_dir / "raw_data" / raw_data_id
    # create folder for raw data
    if not os.path.exists(raw_data_dir):
        os.makedirs(raw_data_dir)

    return raw_data_dir


@router.post("", status_code=status.HTTP_200_OK)
def upload_raw_data(
    request: Request,
    files: UploadFile,
    background_tasks: BackgroundTasks,
    project: models.Project = Depends(deps.can_read_write_project),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    # confirm project and flight exist
    if not project or not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    # upload file info and new filename
    original_filename = Path(files.filename)
    new_filename = str(uuid4())
    # check if uploaded file has supported extension
    suffix = original_filename.suffix
    if suffix != ".zip":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Raw data must be in .zip"
        )
    # create new raw data record
    try:
        raw_data = crud.raw_data.create_with_flight(
            db,
            obj_in=schemas.RawDataCreate(
                original_filename=str(original_filename),
                filepath="null",
            ),
            flight_id=flight.id,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unable to process upload"
        )
    # get path for uploaded raw data directory
    raw_data_dir = Path(
        get_raw_data_dir(str(project.id), str(flight.id), str(raw_data.id))
    )
    # construct fullpath for uploaded raw data
    destination_filepath = raw_data_dir / (new_filename + suffix)
    try:
        # write uploaded raw data to disk
        with open(destination_filepath, "wb") as buffer:
            shutil.copyfileobj(files.file, buffer)
        # add filepath to raw data object
        crud.raw_data.update(
            db,
            db_obj=raw_data,
            obj_in=schemas.RawDataUpdate(filepath=str(destination_filepath)),
        )
    except Exception:
        logger.exception("Failed to process uploaded raw data")
        # clean up any files
        if os.path.exists(destination_filepath):
            os.remove(destination_filepath)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unable to process upload"
        )

    return {"upload-status": "success"}


@router.get("/{raw_data_id}", response_model=schemas.RawData)
def read_data_product(
    request: Request,
    raw_data_id: UUID,
    flight_id: UUID,
    flight: models.Flight = Depends(deps.can_read_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve raw data for flight if user can access it."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
    raw_data = crud.raw_data.get_single_by_id(
        db, raw_data_id=raw_data_id, upload_dir=upload_dir
    )
    return raw_data


@router.get("", response_model=Sequence[schemas.RawData])
def read_all_raw_data(
    request: Request,
    flight_id: UUID,
    flight: models.Flight = Depends(deps.can_read_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve all raw data for flight if user can access it."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
    all_raw_data = crud.raw_data.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=upload_dir
    )
    return all_raw_data


@router.delete("/{raw_data_id}", response_model=schemas.RawData)
def deactivate_raw_data(
    raw_data_id: UUID,
    project: models.Project = Depends(deps.can_read_write_project),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if not project.is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden"
        )
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    deactivated_raw_data = crud.raw_data.deactivate(db, raw_data_id=raw_data_id)
    if not deactivated_raw_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to deactivate"
        )
    return deactivated_raw_data
