import os
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.utils.tusd.post_processing import (
    process_data_product_uploaded_to_tusd,
    process_raw_data_uploaded_to_tusd,
)
from app.schemas import TUSDHook


router = APIRouter()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def handle_tusd_http_hooks(
    payload: TUSDHook,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_approved_user),
) -> Any:
    """Receives http hook requests from tusd server. Starts process for moving data
    from tusd server storage to backend static file directory.

    Args:
        payload (TUSDHook): Request from tusd.
        db (Session, optional): Database session. Defaults to Depends(deps.get_db).
        current_user (models.User, optional): User that innitiated upload to tusd. Defaults to Depends(deps.get_current_approved_user).

    Raises:
        HTTPException: Raised if missing X-Data-Type header.
        HTTPException: Raised if missing X-Project-ID header.
        HTTPException: Raised if missing X-Flight-ID header.
        HTTPException: Raised if user cannot access project.
        HTTPException: Raised if flight not found.
        HTTPException: Raised if uploaded file not found in tusd server storage.
    """
    # get data type from custom header
    x_data_type = payload.Event.HTTPRequest.Header.X_Data_Type
    if not x_data_type or len(x_data_type) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must include 'X-Data-Type' header with single valid data type",
        )
    data_type = x_data_type[0]
    # get project id from custom header
    x_project_id = payload.Event.HTTPRequest.Header.X_Project_ID
    if not x_project_id or len(x_project_id) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must include 'X-Project-Id' header with single valid project id",
        )
    project_id = x_project_id[0]
    # get flight id from custom header
    x_flight_id = payload.Event.HTTPRequest.Header.X_Flight_ID
    if not x_flight_id or len(x_flight_id) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must include 'X-Flight-Id' header with single valid flight id",
        )
    flight_id = x_flight_id[0]
    # check if user has permission to read/write to project
    project = deps.can_read_write_project(
        db=db, project_id=project_id, current_user=current_user
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    # confirm provided flight id belongs to project
    flight = crud.flight.get(db, id=flight_id)
    if not flight or flight.project_id != project.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )

    # tusd http hooks
    # other possible hooks: pre-create, post-create, post-receive

    # non-blocking, runs when upload to tusd server completed
    if payload.Type == "post-finish":
        # verify uploaded file exists in tusd data dir
        storage = payload.Event.Upload.Storage
        if storage and os.path.exists(storage.Path):
            # post-processing for geotiffs and point clouds
            if data_type != "raw":
                process_data_product_uploaded_to_tusd(
                    db,
                    current_user=current_user,
                    storage_path=Path(storage.Path),
                    original_filename=Path(payload.Event.Upload.MetaData.filename),
                    dtype=data_type,
                    project_id=project.id,
                    flight_id=flight.id,
                )
            else:
                process_raw_data_uploaded_to_tusd(
                    db,
                    current_user=current_user,
                    storage_path=Path(storage.Path),
                    original_filename=Path(payload.Event.Upload.MetaData.filename),
                    dtype=data_type,
                    project_id=project.id,
                    flight_id=flight.id,
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file not found"
            )
