import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.api_v1.endpoints.data_products import get_data_product_dir
from app.api.api_v1.endpoints.raw_data import get_raw_data_dir
from app.tasks import (
    convert_las_to_copc,
    create_point_cloud_preview_image,
    process_geotiff,
    process_raw_data,
)


logger = logging.getLogger("__name__")


def process_data_product_uploaded_to_tusd(
    db: Session,
    current_user: models.User,
    storage_path: Path,
    original_filename: Path,
    dtype: str,
    project_id: UUID,
    flight_id: UUID,
) -> dict:
    """Post-processing method for data product uploaded to tus file server. Creates job
    for converting GeoTIFF (.tif) to Cloud Optimized GeoTIFF or converting point cloud
    (.las) to Cloud Optimized Point Cloud. Returns "processing" status if the job is
    successfully started.

    Args:
        db (Session): Database session.
        current_user (models.User): User that uploaded the data product.
        storage_path (Path): Location of data product on tus file server.
        original_filename (Path): Original name of uploaded data product.
        dtype (str): Type of data product (e.g., ortho, dsm, etc.)
        project_id (UUID): Project ID for data product's project.
        flight_id (UUID): Flight ID for data product's flight.

    Raises:
        HTTPException: Raised if file extension is not supported.
        HTTPException: Raised if unable to create job.

    Returns:
        dict: Processing status.
    """
    # create new filename
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
        flight_id=flight_id,
    )
    # get path for uploaded data product directory
    data_product_dir = get_data_product_dir(
        str(project_id), str(flight_id), str(data_product.id)
    )
    # construct fullpath for uploaded data product
    tmpdir = tempfile.mkdtemp(dir=data_product_dir)
    destination_filepath = f"{tmpdir}/{new_filename}{suffix}"

    # create job to track task progress
    job_in = schemas.job.JobCreate(
        name="upload-data-product",
        state="PENDING",
        status="WAITING",
        start_time=datetime.now(),
        data_product_id=data_product.id,
    )
    job = crud.job.create_job(db, job_in)

    if dtype == "point_cloud":
        # start point cloud process in background
        res = convert_las_to_copc.apply_async(
            args=(
                original_filename.name,
                str(storage_path),
                destination_filepath,
                project_id,
                flight_id,
                job.id,
                data_product.id,
            ),
            link=create_point_cloud_preview_image.s(),
        )
    else:
        # start geotiff process in background
        process_geotiff.apply_async(
            args=(
                original_filename.name,
                str(storage_path),
                destination_filepath,
                current_user.id,
                project_id,
                flight_id,
                job.id,
                data_product.id,
            ),
        )

    return {"status": "processing"}


def process_raw_data_uploaded_to_tusd(
    db: Session,
    current_user: models.User,
    storage_path: Path,
    original_filename: Path,
    dtype: str,
    project_id: UUID,
    flight_id: UUID,
) -> dict:
    """Post-processing method for raw_data uploaded to tus file server. Moves uploaded
    zip to static file location and creates record in database. Returns "success"
    status if the upload process completes.

    Args:
        db (Session): Database session.
        current_user (models.User): User that uploaded the data product.
        storage_path (Path): Location of data product on tus file server.
        original_filename (Path): Original name of uploaded data product.
        dtype (str): Type of data product (e.g., ortho, dsm, etc.)
        project_id (UUID): Project ID for data product's project.
        flight_id (UUID): Flight ID for data product's flight.

    Raises:
        HTTPException: Raised if file extension is not supported.
        HTTPException: Raised if unable to create raw data record.
        HTTPException: Raised if unable to update raw data record.

    Returns:
        dict: Processing status.
    """
    # upload file info and new filename
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
            flight_id=flight_id,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unable to process upload"
        )
    # get path for uploaded raw data directory
    raw_data_dir = Path(
        get_raw_data_dir(str(project_id), str(flight_id), str(raw_data.id))
    )
    # construct fullpath for uploaded raw data
    destination_filepath = raw_data_dir / (new_filename + suffix)

    # create job to track task progress
    job_in = schemas.job.JobCreate(
        name="upload-raw-data",
        state="PENDING",
        status="WAITING",
        start_time=datetime.now(),
        raw_data_id=raw_data.id,
    )
    job = crud.job.create_job(db, job_in)

    # start copying raw data from tusd to static files in background
    process_raw_data.apply_async(
        args=(raw_data.id, str(storage_path), str(destination_filepath), job.id)
    )

    return {"status": "processing"}
