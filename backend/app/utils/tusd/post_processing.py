import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.api_v1.endpoints.raw_data import get_raw_data_dir
from app.api.utils import get_data_product_dir
from app.schemas.job import State, Status
from app.tasks.post_upload_tasks import generate_point_cloud_preview
from app.tasks.upload_tasks import (
    upload_geotiff,
    upload_panoramic,
    upload_point_cloud,
    upload_raw_data,
)

logger = logging.getLogger("__name__")

SUPPORTED_EXTENSIONS = {
    ".tif",
    ".las",
    ".laz",
    ".copc.laz",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".avif",
}


def get_file_extension(filename: Path) -> str:
    """Get the file extension, handling compound extensions like .copc.laz.

    Args:
        filename (Path): The filename to check

    Returns:
        str: The full extension including compound extensions
    """
    name = filename.name.lower()
    if name.endswith(".copc.laz"):
        return ".copc.laz"
    elif name.endswith(".laz"):
        return ".laz"
    elif name.endswith(".las"):
        return ".las"
    elif name.endswith(".tif"):
        return ".tif"
    return filename.suffix.lower()


def process_data_product_uploaded_to_tusd(
    db: Session,
    user_id: UUID,
    storage_path: Path,
    original_filename: Path,
    dtype: str,
    project_id: UUID,
    flight_id: UUID,
    project_to_utm: bool = False,
) -> dict:
    """Post-processing method for data product uploaded to tus file server. Creates job
    for converting GeoTIFF (.tif) to Cloud Optimized GeoTIFF or converting point cloud
    (.las) to Cloud Optimized Point Cloud. Returns "processing" status if the job is
    successfully started.

    Args:
        db (Session): Database session.
        user_id (UUID): User ID for uploaded the data product.
        storage_path (Path): Location of data product on tus file server.
        original_filename (Path): Original name of uploaded data product.
        dtype (str): Type of data product (e.g., ortho, dsm, etc.)
        project_id (UUID): Project ID for data product's project.
        flight_id (UUID): Flight ID for data product's flight.
        project_to_utm (bool): Whether to project the GeoTIFF to UTM.

    Raises:
        HTTPException: Raised if file extension is not supported.
        HTTPException: Raised if unable to create job.

    Returns:
        dict: Processing status.
    """
    # create new filename
    new_filename = str(uuid4())
    # get the full extension
    extension = get_file_extension(original_filename)
    # check if uploaded file has supported extension
    if extension not in SUPPORTED_EXTENSIONS:
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
    destination_filepath = f"{tmpdir}/{new_filename}{extension}"

    # create job to track task progress
    job_in = schemas.job.JobCreate(
        name="upload-data-product",
        state=State.PENDING,
        status=Status.WAITING,
        start_time=datetime.now(tz=timezone.utc),
        data_product_id=data_product.id,
    )
    job = crud.job.create_job(db, job_in)

    if dtype == "point_cloud":
        # start point cloud process in background
        upload_point_cloud.apply_async(
            args=(str(storage_path), destination_filepath, job.id, data_product.id),
            link=generate_point_cloud_preview.s(),
        )
    elif dtype == "panoramic":
        # start panoramic process in background
        upload_panoramic.apply_async(
            args=(str(storage_path), destination_filepath, job.id, data_product.id),
        )
    else:
        # start geotiff process in background
        upload_geotiff.apply_async(
            args=(
                str(storage_path),
                destination_filepath,
                user_id,
                job.id,
                data_product.id,
                project_to_utm,
            ),
        )

    return {"status": "processing"}


def process_raw_data_uploaded_to_tusd(
    db: Session,
    user_id: UUID,
    storage_path: Path,
    original_filename: Path,
    project_id: UUID,
    flight_id: UUID,
) -> dict:
    """Post-processing method for raw_data uploaded to tus file server. Moves uploaded
    zip to static file location and creates record in database. Returns "success"
    status if the upload process completes.

    Args:
        db (Session): Database session.
        user_id (UUID): User ID for uploaded the raw data.
        storage_path (Path): Location of data product on tus file server.
        original_filename (Path): Original name of uploaded raw data.
        project_id (UUID): Project ID for raw data's project.
        flight_id (UUID): Flight ID for raw data's flight.

    Raises:
        HTTPException: Raised if file extension is not supported.
        HTTPException: Raised if unable to create raw data record.
        HTTPException: Raised if unable to update raw data record.

    Returns:
        dict: Processing status.
    """
    # upload file info and new filename
    new_filename = str(uuid4())
    # lowercase the file extension
    original_filename = original_filename.with_suffix(original_filename.suffix.lower())
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
        state=State.PENDING,
        status=Status.WAITING,
        start_time=datetime.now(tz=timezone.utc),
        raw_data_id=raw_data.id,
    )
    job = crud.job.create_job(db, job_in)

    # start copying raw data from tusd to static files in background
    upload_raw_data.apply_async(
        args=(
            raw_data.id,
            str(storage_path),
            str(destination_filepath),
            job.id,
            project_id,
            user_id,
        )
    )

    return {"status": "processing"}
