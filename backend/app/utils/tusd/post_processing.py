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
from app.tasks import process_geotiff, process_point_cloud


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
    # copy uploaded data product to static files and create new job
    shutil.copyfile(storage_path, destination_filepath)
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
                project_id,
                flight_id,
                job.id,
                data_product.id,
            ],
            kwargs={},
            queue="main-queue",
        )
    else:
        # start geotiff process in background
        process_geotiff.apply_async(
            args=[
                original_filename.name,
                destination_filepath,
                current_user.id,
                project_id,
                flight_id,
                job.id,
                data_product.id,
            ],
            kwargs={},
            queue="main-queue",
        )

    # remove data product from tusd
    try:
        # remove zip file
        os.remove(storage_path)
        # remove zip file metadata
        os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")

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
    try:
        # copy uploaded raw data to static files and update record
        shutil.copyfile(storage_path, destination_filepath)
        # add filepath to raw data object
        crud.raw_data.update(
            db,
            db_obj=raw_data,
            obj_in=schemas.RawDataUpdate(filepath=str(destination_filepath)),
        )
    except Exception:
        logger.exception("Failed to process uploaded raw data")
        # clean up any files
        if os.path.exists(destination_filepath):
            os.remove(destination_filepath)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unable to process upload"
        )

    # remove raw data from tusd
    try:
        # remove zip file
        os.remove(storage_path)
        # remove zip file metadata
        os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")

    return {"status": "success"}
