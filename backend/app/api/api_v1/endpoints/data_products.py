import os
import pathlib
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
from app.worker import process_geotiff, process_point_cloud
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

    if dtype not in ["dsm", "ortho", "point_cloud"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown data type"
        )

    if request.client and request.client.host == "testclient":
        upload_dir = f"{settings.TEST_STATIC_DIR}/projects/{project.id}/flights/{flight.id}/{dtype}"
    else:
        upload_dir = (
            f"{settings.STATIC_DIR}/projects/{project.id}/flights/{flight.id}/{dtype}"
        )

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    file_ext = pathlib.Path(files.filename).suffix
    if dtype == "point_cloud":
        out_path = os.path.join(upload_dir, f"{str(uuid4())}{file_ext}")
    else:
        out_path = os.path.join(upload_dir, f"{str(uuid4())}__temp{file_ext}")

    if file_ext not in [".tif", ".las", ".laz"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file extension"
        )

    with open(out_path, "wb") as buffer:
        shutil.copyfileobj(files.file, buffer)
        job_in = schemas.job.JobCreate(
            name="upload-data-products",
            state="PENDING",
            status="WAITING",
            start_time=datetime.now(),
        )
        job = crud.job.create_job(db, job_in)

    if dtype == "dsm" or dtype == "ortho":
        process_geotiff.apply_async(
            args=[
                files.filename,
                out_path,
                current_user.id,
                project.id,
                flight.id,
                job.id,
                dtype,
            ],
            kwargs={},
            queue="main-queue",
        )
    elif dtype == "point_cloud":
        process_point_cloud.apply_async(
            args=[files.filename, out_path, project.id, flight.id, job.id, dtype],
            kwargs={},
            queue="main-queue",
        )
    else:
        crud.job.update(
            db,
            db_obj=job,
            obj_in=schemas.JobUpdate(
                state="COMPLETED", status="FAILED", end_time=datetime.now()
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown data type"
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
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
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
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
    all_data_product = crud.data_product.get_multi_by_flight(
        db, flight_id=flight.id, upload_dir=upload_dir, user_id=current_user.id
    )
    return all_data_product


@router.post(
    "/{data_product_id}/style",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserStyle,
)
def create_user_style(
    data_product_id: UUID,
    user_style_in: schemas.UserStyleCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create user style settings for a data product."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    existing_user_style = crud.user_style.get_by_data_product_and_user(
        db, data_product_id=data_product_id, user_id=current_user.id
    )
    if existing_user_style:
        raise HTTPException(
            status_code=status.HTTP_400_NOT_FOUND, detail="User style already exists"
        )
    user_style = crud.user_style.create_with_data_product_and_user(
        db,
        obj_in=user_style_in,
        data_product_id=data_product_id,
        user_id=current_user.id,
    )
    return user_style


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


@router.delete("/{data_product_id}", response_model=schemas.DataProduct)
def deactivate_data_product(
    data_product_id: UUID,
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
    deactivated_data_product = crud.data_product.deactivate(
        db, data_product_id=data_product_id
    )
    if not deactivated_data_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to deactivate"
        )
    return deactivated_data_product
