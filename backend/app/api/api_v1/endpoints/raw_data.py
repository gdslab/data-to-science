import logging
import os
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()


logger = logging.getLogger("__name__")


def get_raw_data_dir(project_id: str, flight_id: str, raw_data_id: str) -> Path:
    """Construct path to directory that will store uploaded raw data.

    Args:
        project_id (str): Project ID associated with raw data.
        flight_id (str): Flight ID associated with raw data.
        raw_data_id (str): ID for raw data.

    Returns:
        Path: Full path to raw data directory.
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


@router.get("/{raw_data_id}", response_model=schemas.RawData)
def read_raw_data(
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


@router.get("/{raw_data_id}/download")
def download_raw_data(
    raw_data_id: UUID,
    flight: models.Flight = Depends(deps.can_read_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
    raw_data = crud.raw_data.get_single_by_id(
        db, raw_data_id=raw_data_id, upload_dir=upload_dir
    )
    if not raw_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Raw data not found"
        )
    return FileResponse(
        raw_data.filepath,
        filename=raw_data.original_filename,
        media_type="application/zip",
    )


@router.get("", response_model=Sequence[schemas.RawData])
def read_all_raw_data(
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
