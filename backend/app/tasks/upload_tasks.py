"""Celery tasks for processing uploaded files."""

import os
import shutil
import subprocess
from pathlib import Path
from uuid import UUID

import geopandas as gpd
from celery.utils.log import get_task_logger
from fastapi.encoders import jsonable_encoder

from app import crud, schemas
from app.api.deps import get_db
from app.api.utils import is_geometry_match
from app.core.celery_app import celery_app
from app.utils.job_manager import JobManager
from app.schemas.data_product import DataProductUpdate
from app.schemas.job import Status
from app.utils.ImageProcessor import ImageProcessor


logger = get_task_logger(__name__)

# 32 MB buffer size for copying files
BUFFER_SIZE = 32 * 1024 * 1024


@celery_app.task(name="upload_geotiff_task")
def upload_geotiff(
    storage_path: str,
    geotiff_filepath: str,
    user_id: UUID,
    job_id: UUID,
    data_product_id: UUID,
) -> None:
    """Celery task for processing an uploaded GeoTIFF.

    Args:
        storage_path (Path): Filepath for GeoTIFF in tusd storage.
        geotiff_filepath (str): Filepath for GeoTIFF.
        user_id (UUID): User ID for user that uploaded GeoTIFF.
        job_id (UUID): Job ID for job associated with upload process.
        data_product_id (UUID): Data product ID for uploaded GeoTIFF.
    """
    in_raster = Path(geotiff_filepath)

    # copy uploaded GeoTIFF to static files
    with open(storage_path, "rb") as src, open(in_raster, "wb") as dst:
        shutil.copyfileobj(src, dst, length=BUFFER_SIZE)

    # get database session
    db = next(get_db())
    # retrieve job associated with this task
    try:
        job = JobManager(job_id=job_id)
    except ValueError:
        # remove uploaded file and raise exception
        if os.path.exists(in_raster):
            shutil.rmtree(in_raster.parent)
        logger.error("Could not find job in DB for upload process")
        return None

    # retrieve data product associated with this task
    data_product = crud.data_product.get(db, id=data_product_id)

    if not data_product:
        # remove uploaded file and raise exception
        if os.path.exists(in_raster):
            shutil.rmtree(in_raster.parent)

        job.update(status=Status.FAILED)
        logger.error("Could not find data product in DB for upload process")
        return None

    # update job status to indicate process has started
    job.start()

    # create get STAC properties and convert to COG (if needed)
    try:
        ip = ImageProcessor(str(in_raster))
        out_raster = ip.run()
        default_symbology = ip.get_default_symbology()
    except Exception:
        if os.path.exists(in_raster.parents[1]):
            shutil.rmtree(in_raster.parents[1])
        job.update(status=Status.FAILED)
        logger.exception("Failed to process uploaded GeoTIFF")
        return None

    # update data product with STAC properties
    try:
        crud.data_product.update(
            db,
            db_obj=data_product,
            obj_in=DataProductUpdate(
                filepath=str(out_raster),
                stac_properties=jsonable_encoder(ip.stac_properties),
            ),
        )
    except Exception:
        if os.path.exists(in_raster.parents[1]):
            shutil.rmtree(in_raster.parents[1])
        job.update(status=Status.FAILED)
        logger.exception("Failed to update data product in db")
        return None

    # indicate initial processing finished without errors
    crud.data_product.update(
        db,
        db_obj=data_product,
        obj_in=DataProductUpdate(is_initial_processing_completed=True),
    )

    # create user style record for data product and user
    crud.user_style.create_with_data_product_and_user(
        db,
        obj_in=default_symbology,
        data_product_id=data_product.id,
        user_id=user_id,
    )

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)

    # remove the uploaded geotiff from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")

    return None


@celery_app.task(name="upload_point_cloud_task")
def upload_point_cloud(
    storage_path: str,
    las_filepath: str,
    job_id: UUID,
    data_product_id: UUID,
) -> str | None:
    """Celery task for converting uploaded las/laz point cloud to cloud optimized
    point cloud format. Untwine performs the conversion

    Args:
        storage_path (str): Filepath for point cloud in tusd storage.
        las_filepath (str): Filepath for point cloud.
        job_id (UUID): Job ID for job associated with upload process.
        data_product_id (UUID): Data product ID for uploaded point cloud.

    Raises:
        Exception: Raise if EPT or COPG subprocesses fail.
    """
    in_las = Path(las_filepath)

    # copy uploaded point cloud to static files
    with open(storage_path, "rb") as src, open(in_las, "wb") as dst:
        shutil.copyfileobj(src, dst, length=BUFFER_SIZE)

    # get database session
    db = next(get_db())

    # retrieve job associated with this task
    try:
        job = JobManager(job_id=job_id)
    except ValueError:
        # remove uploaded file and raise exception
        if os.path.exists(in_las):
            shutil.rmtree(in_las.parents[1])
        logger.error("Could not find job in DB for upload process")
        return None

    # retrieve data product associated with this task
    data_product = crud.data_product.get(db, id=data_product_id)

    if not data_product:
        # remove uploaded file and raise exception
        if os.path.exists(in_las):
            shutil.rmtree(in_las.parents[1])
        # remove job if exists
        job.update(status=Status.FAILED)
        logger.error("Could not find data product in DB for upload process")
        return None

    # update job status to indicate process has started
    job.start()

    # create cloud optimized point cloud
    try:
        # construct path for compressed COPC
        if in_las.name.endswith(".copc.laz"):
            # skip if already copc laz (note - need to revise to actually verify format)
            copc_laz_filepath = in_las
        else:
            copc_laz_filepath = in_las.parents[1] / in_las.with_suffix(".copc.laz").name

            subprocess.run(
                [
                    "untwine",
                    "--single_file",
                    "-i",
                    in_las,
                    "-o",
                    copc_laz_filepath,
                ]
            )
            # clean up temp directory created by untwine
            if os.path.exists(f"{copc_laz_filepath}_tmp"):
                shutil.rmtree(f"{copc_laz_filepath}_tmp")
    except Exception:
        logger.exception("Failed to build COPC from uploaded point cloud")
        shutil.rmtree(in_las.parents[1])
        job.update(status=Status.FAILED)
        return None

    # update data product filepath to copc.laz
    crud.data_product.update(
        db,
        db_obj=data_product,
        obj_in=DataProductUpdate(
            filepath=str(copc_laz_filepath), is_initial_processing_completed=True
        ),
    )

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)

    # remove originally uploaded las/laz
    if os.path.exists(in_las.parent):
        shutil.rmtree(in_las.parent)

    # remove the uploaded point cloud from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")

    return str(copc_laz_filepath)


@celery_app.task(name="upload_raw_data_task")
def upload_raw_data(
    raw_data_id: UUID,
    storage_path: str,
    destination_filepath: str,
    job_id: UUID,
    project_id: UUID,
    user_id: UUID,
) -> None:
    """Celery task for copying uploaded raw data (.zip) to static files location.

    Args:
        raw_data_id (UUID): ID for raw data record.
        storage_path (Path): Location of raw data on tusd server.
        destination_filepath (Path): Destination in static files directory for raw data.
        job_id (UUID): ID for job tracking task progress.
        project_ID (UUID): ID for project associated with raw data.
        user_id (UUID): ID for user associated with raw data upload.
    """
    # 128 MB buffer size for copying files
    BUFFER_SIZE = 128 * 1024 * 1024

    # get database session
    db = next(get_db())

    # retrieve job associated with this task
    try:
        job = JobManager(job_id=job_id)
    except ValueError:
        logger.error("Could not find job in DB for upload process")
        return None

    # retrieve raw data associated with this task
    raw_data = crud.raw_data.get(db, id=raw_data_id)
    if not raw_data:
        logger.error("Unable to find raw data record")
        return None

    # update job status to indicate process has started
    job.start()
    try:
        # copy uploaded raw data to static files and update record
        with open(storage_path, "rb") as src, open(destination_filepath, "wb") as dst:
            shutil.copyfileobj(src, dst, length=BUFFER_SIZE)

        # add filepath to raw data object
        crud.raw_data.update(
            db,
            db_obj=raw_data,
            obj_in=schemas.RawDataUpdate(
                filepath=str(destination_filepath), is_initial_processing_completed=True
            ),
        )
    except Exception:
        logger.exception("Failed to process uploaded raw data")
        # clean up any files
        if os.path.exists(destination_filepath):
            os.remove(destination_filepath)
        # remove job
        job.update(status=Status.FAILED)
        return None

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)

    # remove raw data from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")


@celery_app.task(name="upload_vector_layer_task")
def upload_vector_layer(
    file_path: str,
    original_file_name: str,
    project_id: UUID,
    job_id: UUID,
) -> None:
    # Max number of allowed features
    # VECTOR_FEATURE_LIMIT = 250000

    # Clean up temp file
    def cleanup(job: JobManager) -> None:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.exception("Unable to cleanup uploaded file")
            job.update(status=Status.FAILED)

    # get database session
    db = next(get_db())
    # retrieve job associated with task
    job = JobManager(job_id=job_id)
    # update job status to indicate process has started
    job.start()

    # confirm uploaded file exists on disk
    try:
        assert os.path.exists(file_path)
    except AssertionError:
        logger.exception("Cannot find uploaded file on disk")
        job.update(status=Status.FAILED)
        return None

    # read uploaded file into geopandas dataframe
    try:
        gdf = gpd.read_file(file_path)
    except Exception:
        logger.exception("Failed to read uploaded vector layer file")
        job.update(status=Status.FAILED)
        cleanup(job)
        return None

    # check number of features
    if len(gdf) == 0:
        logger.error("Uploaded vector layer does not have any features")
        job.update(
            status=Status.FAILED,
            extra={
                "status": 0,
                "detail": "No features. Vector layer must have at least one feature.",
            },
        )

    # check for consistent geometry type
    first_feature_geometry_type = gdf.iloc[0].geometry.geom_type
    for _, row in gdf.iterrows():
        if not is_geometry_match(
            expected_geometry=first_feature_geometry_type,
            actual_geometry=row.geometry.geom_type,
        ):
            logger.error("Inconsistent geometry types in uploaded vector layer")

    # add vector layer to database
    try:
        crud.vector_layer.create_with_project(
            db, file_name=original_file_name, gdf=gdf, project_id=project_id
        )
    except Exception:
        logger.exception("Error occurred while adding vector layer to database")
        job.update(status=Status.FAILED)
        cleanup(job)
        return None

    # remove uploaded file
    cleanup(job)

    # update job to indicate process finished
    job.update(status=Status.SUCCESS)
