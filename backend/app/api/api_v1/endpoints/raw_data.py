import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.schemas.job import State, Status
from app.schemas.raw_data import ImageProcessingQueryParams
from app.tasks import run_raw_data_image_processing
from app.utils.RpcClient import RpcClient

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


def get_upload_dir() -> str:
    """Returns static files directory.

    Returns:
        str: Path to static files directory.
    """
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
    return upload_dir


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
    upload_dir = get_upload_dir()
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
    upload_dir = get_upload_dir()
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


@router.get("", response_model=List[schemas.RawData])
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
    upload_dir = get_upload_dir()
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
    if not hasattr(project, "role") or project.role != "owner":
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


@router.get("/{raw_data_id}/process")
def process_raw_data(
    raw_data_id: UUID,
    ip_settings: ImageProcessingQueryParams = Depends(),
    project: models.Project = Depends(deps.can_read_write_project),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    # must accept disclaimer
    if ip_settings.disclaimer is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must accept conditions to use this feature",
        )

    # check for "image_processing" extension
    required_extension = "image_processing"
    extension = crud.extension.get_extension_by_name(
        db, extension_name=required_extension
    )
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Required "{required_extension}" extension not installed',
        )
    # check if user has permission to run this endpoint (by user.extensions or team.extensions)
    user_has_active_extension = False
    user_extension = crud.extension.get_user_extension(
        db, extension_id=extension.id, user_id=current_user.id
    )
    if user_extension:
        user_has_active_extension = True
    if not user_has_active_extension:
        team_extension_by_user = crud.extension.get_team_extension_by_user(
            db, extension_id=extension.id, user_id=current_user.id
        )
        if team_extension_by_user:
            user_has_active_extension = True

    if not user_has_active_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required extension for this operation",
        )

    # check if a job processing raw data is currently ongoing
    existing_jobs = crud.job.get_by_raw_data_id(
        db, job_name="processing-raw-data", raw_data_id=raw_data_id
    )
    existing_job_still_working = False
    for job in existing_jobs:
        if job.state != State.COMPLETED:
            existing_job_still_working = True
    if existing_job_still_working:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Raw data already being processed",
        )

    # get raw data from db
    raw_data = crud.raw_data.get_single_by_id(
        db, raw_data_id=raw_data_id, upload_dir=get_upload_dir()
    )
    if not raw_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Raw data not found"
        )

    # create job
    job_in = schemas.job.JobCreate(
        name="processing-raw-data",
        state=State.PENDING,
        status=Status.WAITING,
        start_time=datetime.now(tz=timezone.utc),
        raw_data_id=raw_data.id,
    )
    job = crud.job.create_job(db, obj_in=job_in)

    # get required paths from raw data object and environment variables
    upload_dir = get_upload_dir()
    storage_path = raw_data.filepath
    external_storage_dir = os.environ.get("EXTERNAL_STORAGE")
    rabbitmq_host = os.environ.get("RABBITMQ_HOST")

    # only start this workflow if external storage and rabbitmq host are provided
    if external_storage_dir and os.path.isdir(external_storage_dir) and rabbitmq_host:
        run_raw_data_image_processing.apply_async(
            args=(
                external_storage_dir,
                storage_path,
                raw_data.original_filename,
                project.id,
                raw_data.flight_id,
                raw_data.id,
                current_user.id,
                job.id,
                ip_settings.model_dump(),
            )
        )
    else:
        logger.error(
            "Unable to start raw data processing due to unavailable external storage or RabbitMQ service"
        )
        # update job
        job_update_in = schemas.JobUpdate(
            state=State.COMPLETED,
            status=Status.FAILED,
            end_time=datetime.now(tz=timezone.utc),
        )
        crud.job.update(db, db_obj=job, obj_in=job_update_in)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to start request",
        )

    # send response back to client
    return {"job_id": job.id}


@router.get("/{raw_data_id}/check_progress/{job_id}")
def check_raw_data_processing_progress(
    raw_data_id: UUID,
    job_id: UUID,
    project: models.Project = Depends(deps.can_read_write_project),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    # find job with name "processing-raw-data" for raw_data_id
    job = crud.job.get(db, id=job_id)
    if not job or job.name != "processing-raw-data" or job.status != "INPROGRESS":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active job found for processing this raw data",
        )

    # if job exists, check "extra" for key "batch_id"
    if (
        not job.extra
        or not isinstance(job.extra, Dict)
        or not "batch_id" in job.extra.keys()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job does not have required Batch ID",
        )

    # if batch_id exists, use rpcclient to check for progress %
    batch_id = job.extra["batch_id"]
    logger.info(f"Requesting progress for Batch ID: {batch_id}")
    rpc_client = RpcClient(routing_key="raw-data-check-progress-queue")
    progress = rpc_client.call(batch_id)
    rpc_client.connection.close()

    if not progress or float(progress) == -9999:
        job_update_in = schemas.JobUpdate(
            state=State.COMPLETED,
            status=Status.FAILED,
            end_time=datetime.now(tz=timezone.utc),
        )
        crud.job.update(db, db_obj=job, obj_in=job_update_in)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while running job",
        )

    # report back {"progress": str}
    return {"progress": progress}
