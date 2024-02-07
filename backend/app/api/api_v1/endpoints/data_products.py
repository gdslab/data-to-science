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
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.worker import process_geotiff, process_point_cloud, run_toolbox_process
from app.core.config import settings

router = APIRouter()


def get_upload_dir(
    request: Request, projectId: UUID, flightId: UUID, dType: str
) -> str:
    if request.client and request.client.host == "testclient":
        upload_dir = f"{settings.TEST_STATIC_DIR}/projects/{projectId}/flights/{flightId}/{dType}"
    else:
        upload_dir = (
            f"{settings.STATIC_DIR}/projects/{projectId}/flights/{flightId}/{dType}"
        )

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    return upload_dir


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

    upload_dir = get_upload_dir(request, project.id, flight.id, dtype)

    original_filename = pathlib.Path(files.filename)
    unique_filename = str(uuid4())

    if dtype == "point_cloud":
        destination_filepath = os.path.join(
            upload_dir, unique_filename + original_filename.suffix
        )
    else:
        destination_filepath = os.path.join(
            upload_dir, f"{unique_filename}__temp{original_filename.suffix}"
        )

    if original_filename.suffix not in [".tif", ".las", ".laz"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file extension"
        )

    with open(destination_filepath, "wb") as buffer:
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
                original_filename.name,
                destination_filepath,
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
            args=[
                original_filename.name,
                destination_filepath,
                project.id,
                flight.id,
                job.id,
                dtype,
            ],
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
    flight: models.Flight = Depends(deps.can_read_flight),
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
    flight: models.Flight = Depends(deps.can_read_flight),
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


class ProcessingRequest(BaseModel):
    chm: bool
    exg: bool
    exgRed: int
    exgGreen: int
    exgBlue: int
    ndvi: bool
    ndviNIR: int
    ndviRed: int


@router.post("/{data_product_id}/tools", status_code=status.HTTP_202_ACCEPTED)
def run_processing_tool(
    request: Request,
    data_product_id: UUID,
    toolbox_in: ProcessingRequest,
    current_user: models.User = Depends(deps.get_current_approved_user),
    project: models.Project = Depends(deps.can_read_write_project),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not project or not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )

    if toolbox_in.exg is False and toolbox_in.ndvi is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No product selected"
        )

    data_product = crud.data_product.get(db, id=data_product_id)
    if not data_product or not data_product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )

    upload_dir = get_upload_dir(request, project.id, flight.id, data_product.data_type)

    # ndvi
    if toolbox_in.ndvi:
        out_raster = os.path.join(upload_dir, str(uuid4()) + ".tif")

        # create new data product record
        ndvi_data_product = crud.data_product.create_with_flight(
            db,
            schemas.DataProductCreate(
                data_type=data_product.data_type,
                filepath=out_raster,
                original_filename=data_product.original_filename,
            ),
            flight_id=flight.id,
        )

        # run ndvi tool in background
        tool_params = {
            "red_band_idx": toolbox_in.ndviRed,
            "nir_band_idx": toolbox_in.ndviNIR,
        }
        run_toolbox_process.apply_async(
            args=[
                "ndvi",
                data_product.filepath,
                out_raster,
                tool_params,
                ndvi_data_product.id,
                current_user.id,
            ],
            kwargs={},
            queue="main-queue",
        )

    # exg
    pass
