import os
import shutil
from datetime import datetime
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
from app.worker import process_geotiff
from app.core.config import settings

router = APIRouter()


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def upload_raw_data(
    request: Request,
    files: UploadFile,
    background_tasks: BackgroundTasks,
    project: models.Project = Depends(deps.can_read_write_project),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not project or not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    if request.client.host == "testclient":
        upload_dir = (
            f"{settings.TEST_UPLOAD_DIR}/projects/{project.id}/flights{flight.id}"
        )
    else:
        upload_dir = f"{settings.UPLOAD_DIR}/projects/{project.id}/flights/{flight.id}"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    out_path = os.path.join(upload_dir, f"{str(uuid4())}__temp.tif")

    with open(out_path, "wb") as buffer:
        shutil.copyfileobj(files.file, buffer)

    job_in = schemas.job.JobCreate(
        name="upload-raw-data",
        state="PENDING",
        status="WAITING",
        start_time=datetime.now(),
    )
    job = crud.job.create_job(db, job_in)
    process_geotiff.apply_async(
        args=[files.filename, out_path, project.id, flight.id, job.id],
        kwargs={},
        queue="main-queue",
    )

    return {"status": "processing"}


@router.get("/{raw_data_id}", response_model=schemas.RawData)
def read_raw_data(
    request: Request,
    raw_data_id: UUID,
    flight_id: UUID,
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve raw data for flight if user can access it."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    if request.client.host == "testclient":
        upload_dir = settings.TEST_UPLOAD_DIR
    else:
        upload_dir = settings.UPLOAD_DIR
    raw_data = crud.raw_data.get_single_by_id(
        db, raw_data_id=raw_data_id, upload_dir=upload_dir
    )
    return raw_data


@router.get("/", response_model=Sequence[schemas.RawData])
def read_all_raw_data(
    request: Request,
    flight_id: UUID,
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve all raw data for flight if user can access it."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    if request.client.host == "testclient":
        upload_dir = settings.TEST_UPLOAD_DIR
    else:
        upload_dir = settings.UPLOAD_DIR
    all_raw_data = crud.raw_data.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=upload_dir
    )
    return all_raw_data
