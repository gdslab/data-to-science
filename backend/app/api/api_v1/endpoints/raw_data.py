import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List
from uuid import UUID

from celery import chain
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.schemas.image_processing_backend import ImageProcessingBackend
from app.schemas.job import State, Status
from app.schemas.raw_data import ImageProcessingQueryParams
from app.tasks.raw_image_processing_tasks import (
    start_raw_data_processing,
    transfer_raw_data,
)
from app.tasks.utils import is_valid_filename
from app.utils.job_manager import JobManager
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
    # set default image processing backend to ODM
    image_processing_backend = ImageProcessingBackend.ODM

    # check for "image_processing" extension
    required_extension = "image_processing"
    extension = crud.extension.get_extension_by_name(
        db, extension_name=required_extension
    )
    if extension:
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

        if user_has_active_extension:
            image_processing_backend = ImageProcessingBackend.METASHAPE

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
    processing_job = JobManager(job_name="processing-raw-data", raw_data_id=raw_data.id)

    # get required paths from raw data object and environment variables
    storage_path = raw_data.filepath
    external_storage_dir = os.environ.get("EXTERNAL_STORAGE")
    rabbitmq_host = os.environ.get("RABBITMQ_HOST")

    # create name for processing project on remote server
    if isinstance(flight.sensor, Enum):
        sensor = flight.sensor.value
    else:
        sensor = flight.sensor

    prj_name = (
        project.title[:10].strip().replace(" ", "_")
        + "_"
        + flight.acquisition_date.strftime("%Y%m%d")
        + "_"
        + sensor
    )

    if not is_valid_filename(prj_name):
        prj_name = "d2s-project"

    # only start this workflow if external storage and rabbitmq host are provided
    if external_storage_dir and os.path.isdir(external_storage_dir) and rabbitmq_host:
        chain(
            transfer_raw_data.s(
                external_storage_dir,
                storage_path,
                raw_data.original_filename,
                prj_name,
                project.id,
                raw_data.flight_id,
                raw_data.id,
                current_user.id,
                processing_job.job_id,
                image_processing_backend,
                ip_settings.model_dump(),
            )
            | start_raw_data_processing.s(),
        ).apply_async()
    else:
        logger.error(
            "Unable to start raw data processing due to unavailable external storage or RabbitMQ service"
        )
        processing_job.update(status=Status.FAILED)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to start request",
        )

    # send response back to client
    return {"job_id": processing_job.job_id}


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
    try:
        job = JobManager(job_id=job_id)
        job_db_obj = job.job
        assert job_db_obj
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # if job exists, check "extra" for key "batch_id"
    extra = job_db_obj.extra
    if not extra or not isinstance(extra, Dict) or not "batch_id" in extra.keys():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job does not have required Batch ID",
        )

    # if batch_id exists, use rpcclient to check for progress %
    batch_id = extra["batch_id"]
    logger.info(f"Requesting progress for Batch ID: {batch_id}")
    rpc_client = RpcClient(routing_key="raw-data-check-progress-queue")
    progress = rpc_client.call(batch_id)
    rpc_client.connection.close()

    if not progress or float(progress) == -9999:
        job.update(status=Status.FAILED)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while running job",
        )

    # report back {"progress": str}
    return {"progress": progress}
