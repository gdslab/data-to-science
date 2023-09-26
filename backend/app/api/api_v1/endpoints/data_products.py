import os
import shutil
from datetime import datetime
from typing import Any, Sequence
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
    Query,
    UploadFile,
)
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.worker import process_geotiff
from app.core.config import settings

router = APIRouter()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def upload_data_product(
    request: Request,
    files: UploadFile,
    dtype: str = Query(),
    current_user: models.User = Depends(deps.get_current_approved_user),
    project: models.Project = Depends(deps.can_read_write_project),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not project or not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    if request.client and request.client.host == "testclient":
        upload_dir = (
            f"{settings.TEST_UPLOAD_DIR}/projects/{project.id}/flights/{flight.id}"
        )
    else:
        upload_dir = f"{settings.UPLOAD_DIR}/projects/{project.id}/flights/{flight.id}"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    out_path = os.path.join(upload_dir, f"{str(uuid4())}__temp.tif")

    with open(out_path, "wb") as buffer:
        shutil.copyfileobj(files.file, buffer)

    job_in = schemas.job.JobCreate(
        name="upload-data-products",
        state="PENDING",
        status="WAITING",
        start_time=datetime.now(),
    )
    job = crud.job.create_job(db, job_in)
    process_geotiff.apply_async(
        args=[files.filename, out_path, project.id, flight.id, job.id, dtype],
        kwargs={},
        queue="main-queue",
    )

    return {"status": "processing"}


@router.get("/{data_product_id}", response_model=schemas.DataProduct)
def read_data_product(
    request: Request,
    data_product_id: UUID,
    flight_id: UUID,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve raw data for flight if user can access it."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    if request.client and request.client.host == "testclient":
        upload_dir = settings.TEST_UPLOAD_DIR
    else:
        upload_dir = settings.UPLOAD_DIR
    data_product = crud.data_product.get_single_by_id(
        db,
        data_product_id=data_product_id,
        upload_dir=upload_dir,
        user_id=current_user.id,
    )
    return data_product


@router.get("", response_model=Sequence[schemas.DataProduct])
def read_all_data_product(
    request: Request,
    flight_id: UUID,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve all raw data for flight if user can access it."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    if request.client and request.client.host == "testclient":
        upload_dir = settings.TEST_UPLOAD_DIR
    else:
        upload_dir = settings.UPLOAD_DIR
    all_data_product = crud.data_product.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=upload_dir, user_id=current_user.id
    )
    return all_data_product


@router.put("/{data_product_id}/style", response_model=schemas.UserStyle)
def update_user_style(
    data_product_id: UUID,
    user_style_in: schemas.UserStyleUpdate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update user's style settings for a data product."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    current_user_style = crud.user_style.get_by_data_product_and_user(
        db, data_product_id=data_product_id, user_id=current_user.id
    )
    if not current_user_style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User style not found"
        )
    updated_user_style = crud.user_style.update(
        db, db_obj=current_user_style, obj_in=user_style_in
    )
    return updated_user_style
