import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path, PosixPath
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


logger = logging.getLogger("__name__")


def get_data_product_dir(project_id: str, flight_id: str, data_product_id: str) -> str:
    """Construct path to directory that will store uploaded data product.

    Args:
        project_id (str): Project ID associated with data product.
        flight_id (str): Flight ID associated with data product.
        data_product_id (str): ID for data product.

    Returns:
        str: Full path to data product directory.
    """
    # get root static path
    if os.environ.get("RUNNING_TESTS") == "1":
        data_product_dir = Path(settings.TEST_STATIC_DIR)
    else:
        data_product_dir = Path(settings.STATIC_DIR)
    # construct path to project/flight/dataproduct
    data_product_dir = data_product_dir / "projects" / project_id
    data_product_dir = data_product_dir / "flights" / flight_id
    data_product_dir = data_product_dir / "data_products" / data_product_id
    # create folder for data product
    if not os.path.exists(data_product_dir):
        os.makedirs(data_product_dir)

    return data_product_dir


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def upload_data_product(
    request: Request,
    files: UploadFile,
    dtype: str = Query(min_length=2, max_length=16),
    current_user: models.User = Depends(deps.get_current_approved_user),
    project: models.Project = Depends(deps.can_read_write_project),
    flight: models.Flight = Depends(deps.can_read_write_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    # confirm project and flight exist
    if not project or not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    # uploaded file info and new filename
    original_filename = Path(files.filename)
    new_filename = str(uuid4())
    # check if uploaded file has supported extension
    suffix = original_filename.suffix
    if suffix not in [".tif", ".las", ".laz"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file extension"
        )
    # create new data product record
    data_product = crud.data_product.create_with_flight(
        db,
        obj_in=schemas.DataProductCreate(
            data_type=dtype, filepath="null", original_filename=str(original_filename)
        ),
        flight_id=flight.id,
    )
    # get path for uploaded data product directory
    data_product_dir = get_data_product_dir(
        str(project.id), str(flight.id), str(data_product.id)
    )
    # construct fullpath for uploaded data product
    tmpdir = tempfile.mkdtemp(dir=data_product_dir)
    destination_filepath = f"{tmpdir}/{new_filename}{suffix}"
    # write uploaded data product to disk and create new job
    with open(destination_filepath, "wb") as buffer:
        shutil.copyfileobj(files.file, buffer)
        try:
            job_in = schemas.job.JobCreate(
                name="upload-data-product",
                state="PENDING",
                status="WAITING",
                start_time=datetime.now(),
                data_product_id=data_product.id,
            )
            job = crud.job.create_job(db, job_in)
        except Exception:
            logger.exception("Failed to create new job for data product upload")
            # clean up any files written to tmp location and remove data product record
            shutil.rmtree(data_product_dir)
            with db as session:
                session.delete(data_product)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Unable to process upload"
            )

    if dtype == "point_cloud":
        # start point cloud process in background
        process_point_cloud.apply_async(
            args=[
                original_filename.name,
                destination_filepath,
                project.id,
                flight.id,
                job.id,
                data_product.id,
            ],
            kwargs={},
            queue="main-queue",
        )
    else:
        # start geotiff process in background
        try:
            process_geotiff.apply_async(
                args=[
                    original_filename.name,
                    destination_filepath,
                    current_user.id,
                    project.id,
                    flight.id,
                    job.id,
                    data_product.id,
                ],
                kwargs={},
                queue="main-queue",
            )
        except Exception:
            logger.exception("Unable to start upload process geotiff task")
            # clean up any files written to tmp location and remove data product and job
            shutil.rmtree(data_product_dir)
            with db as session:
                session.delete(job)
                session.delete(data_product)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Unable to process upload"
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
    if os.environ.get("RUNNING_TESTS") == "1":
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
    if os.environ.get("RUNNING_TESTS") == "1":
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
    # verify project and flight exist
    if not project or not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    # verify at least one processing tool was selected
    if toolbox_in.exg is False and toolbox_in.ndvi is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No product selected"
        )
    # find existing data product that will be used as input raster
    data_product: models.DataProduct | None = crud.data_product.get(
        db, id=data_product_id
    )
    # verify input raster exists and it is active
    if not data_product or not data_product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    # ndvi
    if toolbox_in.ndvi and not os.environ.get("RUNNING_TESTS") == "1":
        # create new data product record
        ndvi_data_product: models.DataProduct = crud.data_product.create_with_flight(
            db,
            schemas.DataProductCreate(
                data_type="NDVI",
                filepath="null",
                original_filename=data_product.original_filename,
            ),
            flight_id=flight.id,
        )
        # get path for ndvi tool output raster
        data_product_dir: PosixPath = get_data_product_dir(
            str(project.id), str(flight.id), str(ndvi_data_product.id)
        )
        ndvi_filename: str = str(uuid4()) + ".tif"
        out_raster: PosixPath = data_product_dir / ndvi_filename
        # run ndvi tool in background
        tool_params: dict = {
            "red_band_idx": toolbox_in.ndviRed,
            "nir_band_idx": toolbox_in.ndviNIR,
        }
        run_toolbox_process.apply_async(
            args=[
                "ndvi",
                data_product.filepath,
                str(out_raster),
                tool_params,
                ndvi_data_product.id,
                current_user.id,
            ],
            kwargs={},
            queue="main-queue",
        )

    # exg
    if toolbox_in.exg and not os.environ.get("RUNNING_TESTS") == "1":
        # create new data product record
        exg_data_product: models.DataProduct = crud.data_product.create_with_flight(
            db,
            schemas.DataProductCreate(
                data_type="ExG",
                filepath="null",
                original_filename=data_product.original_filename,
            ),
            flight_id=flight.id,
        )
        # get path for exg tool output raster
        data_product_dir: PosixPath = get_data_product_dir(
            str(project.id), str(flight.id), str(exg_data_product.id)
        )
        exg_filename: str = str(uuid4()) + ".tif"
        out_raster: PosixPath = data_product_dir / exg_filename
        # run exg tool in background
        tool_params = {
            "red_band_idx": toolbox_in.exgRed,
            "green_band_idx": toolbox_in.exgGreen,
            "blue_band_idx": toolbox_in.exgBlue,
        }
        run_toolbox_process.apply_async(
            args=[
                "exg",
                data_product.filepath,
                str(out_raster),
                tool_params,
                exg_data_product.id,
                current_user.id,
            ],
            kwargs={},
            queue="main-queue",
        )
