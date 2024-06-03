import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TypedDict
from uuid import UUID

import geopandas as gpd
import rasterio
from celery.utils.log import get_task_logger
from geojson_pydantic import FeatureCollection
from rasterstats import zonal_stats

from app import crud, models, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.schemas.data_product import DataProduct, DataProductUpdate
from app.schemas.data_product_metadata import ZonalStatistics
from app.schemas.job import JobUpdate

from app.utils import gen_preview_from_pointcloud
from app.utils.ImageProcessor import ImageProcessor
from app.utils.Toolbox import Toolbox


logger = get_task_logger(__name__)


# Schedule periodic tasks here
# celery_app.conf.beat_schedule = {
#     "print-hello-every-10s": {"task": "tasks.test", "schedule": 10.0, "args": ("hello")}
# }


# @celery_app.task
# def test(arg):
#     print(arg)


@celery_app.task(name="toolbox_task")
def run_toolbox_process(
    tool_name: str,
    in_raster: str,
    out_raster: str,
    params: dict,
    new_data_product_id: UUID,
    user_id: UUID,
) -> None:
    """Celery task for a toolbox process.

    Args:
        tool_name (str): Name of tool to run.
        in_raster (str): Path to input raster.
        out_raster (str): Path for output raster.
        params (dict): Input parameters required by tool.
        new_data_product_id (UUID): Data product ID for output raster.
        user_id (UUID): ID of user creating the data product.
    """
    # database session for updating data product and job tables
    db = next(get_db())

    # create new job for tool process
    job = update_job_status(
        job=None,
        state="CREATE",
        data_product_id=new_data_product_id,
        name=tool_name,
    )

    try:
        update_job_status(job=job, state="INPROGRESS")
        # run tool - a COG will also be produced for the tool output
        toolbox = Toolbox(in_raster, out_raster)
        out_raster, ip = toolbox.run(tool_name, params)
    except Exception:
        logger.exception("Unable to complete tool process")
        update_job_status(job=job, state="ERROR")
        return None

    try:
        new_data_product = crud.data_product.get(db, id=new_data_product_id)
        if new_data_product and os.path.exists(out_raster) and ip:
            default_symbology = ip.get_default_symbology()
            # update data product record with stac properties
            crud.data_product.update(
                db,
                db_obj=new_data_product,
                obj_in=DataProductUpdate(
                    filepath=out_raster, stac_properties=ip.stac_properties
                ),
            )
            # create user style record with default symbology settings
            crud.user_style.create_with_data_product_and_user(
                db,
                obj_in=default_symbology,
                data_product_id=new_data_product.id,
                user_id=user_id,
            )
    except Exception:
        logger.exception("Unable to update data product and create user style")
        update_job_status(job=job, state="ERROR")
        return None

    update_job_status(job=job, state="DONE")


@celery_app.task(name="geotiff_upload_task")
def process_geotiff(
    original_filename: str,
    storage_path: str,
    geotiff_filepath: str,
    user_id: UUID,
    project_id: UUID,
    flight_id: UUID,
    job_id: UUID,
    data_product_id: UUID,
) -> None:
    """Celery task for processing an uploaded GeoTIFF.

    Args:
        original_filename (str): Original filename for GeoTIFF.
        storage_path (Path): Filepath for GeoTIFF in tusd storage.
        geotiff_filepath (str): Filepath for GeoTIFF.
        user_id (UUID): User ID for user that uploaded GeoTIFF.
        project_id (UUID): Project ID associated with data product.
        flight_id (UUID): Flight ID associated with data product.
        job_id (UUID): Job ID for job associated with upload process.
        data_product_id (UUID): Data product ID for uploaded GeoTIFF.
    """
    in_raster = Path(geotiff_filepath)
    # copy uploaded point cloud to static files
    shutil.copyfile(storage_path, in_raster)
    # get database session
    db = next(get_db())
    # retrieve job associated with this task
    job = crud.job.get(db, id=job_id)
    # retrieve data product associated with this task
    data_product = crud.data_product.get(db, id=data_product_id)

    if not job:
        # remove uploaded file and raise exception
        if os.path.exists(in_raster):
            shutil.rmtree(in_raster.parent)
        logger.error("Could not find job in DB for upload process")
        return None

    if not data_product:
        # remove uploaded file and raise exception
        if os.path.exists(in_raster):
            shutil.rmtree(in_raster.parent)
        # remove job if exists
        if job:
            update_job_status(job, state="ERROR")
        logger.error("Could not find data product in DB for upload process")
        return None

    # update job status to indicate process has started
    update_job_status(job, state="INPROGRESS")

    # create get STAC properties and convert to COG (if needed)
    try:
        ip = ImageProcessor(str(in_raster))
        out_raster = ip.run()
        default_symbology = ip.get_default_symbology()
    except Exception as e:
        if os.path.exists(in_raster.parents[1]):
            shutil.rmtree(in_raster.parents[1])
        update_job_status(job, state="ERROR")
        logger.exception("Failed to process uploaded GeoTIFF")
        return None

    # update data product with STAC properties
    crud.data_product.update(
        db,
        db_obj=data_product,
        obj_in=DataProductUpdate(
            filepath=str(out_raster), stac_properties=ip.stac_properties
        ),
    )

    # create user style record for data product and user
    crud.user_style.create_with_data_product_and_user(
        db,
        obj_in=default_symbology,
        data_product_id=data_product.id,
        user_id=user_id,
    )

    # update job to indicate process finished
    update_job_status(job, state="DONE")

    # remove the uploaded geotiff from tusd
    try:
        os.remove(storage_path)
        os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")

    return None


@celery_app.task(name="point_cloud_preview_image_task")
def create_point_cloud_preview_image(in_las: str) -> None:
    """Celery task for creating a preview image for a point cloud.

    Args:
        in_las (str): Path to point cloud.
    """
    # create preview image with uploaded point cloud
    try:
        in_las = Path(in_las)
        if in_las.name.endswith(".copc.laz"):
            preview_out_path = in_las.parents[0] / in_las.name.replace(
                ".copc.laz", ".png"
            )
        else:
            preview_out_path = in_las.parents[0] / in_las.with_suffix(".png").name
        gen_preview_from_pointcloud.create_preview_image(
            input_las_path=in_las,
            preview_out_path=preview_out_path,
        )
    except Exception as e:
        logger.exception("Unable to generate preview image for uploaded point cloud")
        # if this file is present the preview image generation will be skipped next time
        with open(Path(in_las).parent / "preview_failed", "w") as preview:
            pass


@celery_app.task(name="point_cloud_upload_task")
def convert_las_to_copc(
    original_filename: str,
    storage_path: str,
    las_filepath: str,
    project_id: UUID,
    flight_id: UUID,
    job_id: UUID,
    data_product_id: UUID,
) -> str | None:
    """Celery task for converting uploaded las/laz point cloud to cloud optimized
    point cloud format. Untwine performs the conversion

    Args:
        original_filename (str): Original filename for point cloud.
        storage_path (str): Filepath for point cloud in tusd storage.
        las_filepath (str): Filepath for point cloud.
        project_id (UUID): Project ID associated with data product.
        flight_id (UUID): Flight ID associated with data product.
        job_id (UUID): Job ID for job associated with upload process.
        data_product_id (UUID): Data product ID for uploaded point cloud.

    Raises:
        Exception: Raise if EPT or COPG subprocesses fail.
    """
    in_las = Path(las_filepath)
    # copy uploaded point cloud to static files
    shutil.copyfile(storage_path, in_las)
    # get database session
    db = next(get_db())
    # retrieve job associated with this task
    job = crud.job.get(db, id=job_id)
    # retrieve data product associated with this task
    data_product = crud.data_product.get(db, id=data_product_id)

    if not job:
        # remove uploaded file and raise exception
        if os.path.exists(in_las):
            shutil.rmtree(in_las.parents[1])
        logger.error("Could not find job in DB for upload process")
        return None

    if not data_product:
        # remove uploaded file and raise exception
        if os.path.exists(in_las):
            shutil.rmtree(in_las.parents[1])
        # remove job if exists
        if job:
            update_job_status(job, state="ERROR")
        logger.error("Could not find data product in DB for upload process")
        return None

    # update job status to indicate process has started
    update_job_status(job, state="INPROGRESS")

    # create cloud optimized point cloud
    try:
        # construct path for compressed COPC
        if in_las.name.endswith(".copc.laz"):
            # skip if already copc laz (note - need to revise to actually verify format)
            copc_laz_filepath = in_las
        else:
            copc_laz_filepath = in_las.parents[1] / in_las.with_suffix(".copc.laz").name

            result = subprocess.run(
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
    except Exception as e:
        logger.exception("Failed to build COPC from uploaded point cloud")
        shutil.rmtree(in_las.parents[1])
        update_job_status(job, state="ERROR")
        return None

    # update data product filepath to copc.laz
    crud.data_product.update(
        db,
        db_obj=data_product,
        obj_in=DataProductUpdate(filepath=str(copc_laz_filepath)),
    )

    # update job to indicate process finished
    update_job_status(job, state="DONE")

    # remove originally uploaded las/laz
    if os.path.exists(in_las.parent):
        shutil.rmtree(in_las.parent)

    # remove the uploaded point cloud from tusd
    try:
        os.remove(storage_path)
        os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")

    return str(copc_laz_filepath)


@celery_app.task(name="raw_data_upload_task")
def process_raw_data(
    raw_data_id: UUID,
    storage_path: str,
    destination_filepath: str,
    job_id: UUID,
) -> None:
    """Celery task for copying uploaded raw data (.zip) to static files location.

    Args:
        raw_data_id (UUID): ID for raw data record.
        storage_path (Path): Location of raw data on tusd server.
        destination_filepath (Path): Destination in static files directory for raw data.
        job_id (UUID): ID for job tracking task progress.

    Raises:
        HTTPException: Raised if copyfile process fails.
    """
    # get database session
    db = next(get_db())
    # retrieve job associated with this task
    job = crud.job.get(db, id=job_id)
    # retrieve raw data associated with this task
    raw_data = crud.raw_data.get(db, id=raw_data_id)
    # update job status to indicate process has started
    update_job_status(job, state="INPROGRESS")
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
        # remove job
        update_job_status(job, state="ERROR")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unable to process upload"
        )

    # update job to indicate process finished
    update_job_status(job, state="DONE")

    # remove raw data from tusd
    try:
        # remove zip file
        os.remove(storage_path)
        # remove zip file metadata
        os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception("Unable to cleanup upload on tusd server")


@celery_app.task(name="zonal_statistics_task")
def generate_zonal_statistics(
    input_raster: str, zone_feature: str
) -> list[ZonalStatistics]:
    with rasterio.open(input_raster) as src:
        # read first band into array
        data = src.read(1)
        # affine transformation
        affine = src.transform
        # read zone feature geojson and update crs to match src crs
        zone = gpd.read_file(zone_feature, driver="GeoJSON")
        zone = zone.to_crs(src.crs)
        # get stats for zone
        stats = zonal_stats(zone, data, affine=affine)

    return stats


@celery_app.task(name="zonal_statistics_bulk_task")
def generate_zonal_statistics_bulk(
    input_raster: str, data_product_id: UUID, layer_id: UUID, feature_collection: str
) -> list[ZonalStatistics]:
    # database session for updating data product and job tables
    db = next(get_db())

    # create new job for tool process
    job = update_job_status(
        job=None,
        state="CREATE",
        data_product_id=data_product_id,
        name="zonal",
    )

    try:
        update_job_status(job=job, state="INPROGRESS")
        all_zonal_stats = generate_zonal_statistics(input_raster, feature_collection)
    except Exception:
        logger.exception("Unable to complete tool process")
        update_job_status(job=job, state="ERROR")
        return None

    try:
        # deserialize feature collection
        feature_collection = FeatureCollection(**json.loads(feature_collection))
        features = feature_collection.features
        # create metadata record for each zone
        for index, zonal_stats in enumerate(all_zonal_stats):
            metadata_in = schemas.DataProductMetadataCreate(
                category="zonal",
                properties={"stats": zonal_stats},
                vector_layer_id=features[index].properties.id,
            )
            crud.data_product_metadata.create_with_data_product(
                db, obj_in=metadata_in, data_product_id=data_product_id
            )
    except Exception:
        logger.exception("Unable to save zonal statistics")
        update_job_status(job=job, state="ERROR")
        return None

    # update job to indicate process finished
    update_job_status(job, state="DONE")

    return all_zonal_stats


def update_job_status(
    job: models.Job | None,
    state: str,
    data_product_id: UUID | None = None,
    name: str = "unknown",
) -> models.Job | None:
    """Update job table with changes to a task's status.

    Args:
        job (models.Job | None): Existing job object or none if this is a new job.
        state (str): State to update on job.
        data_product_id (UUID | None, optional): _description_. Defaults to None. Data product id (only required to create a job).
        name (str, optional): _description_. Defaults to "unknown". Tool name (if applicable).

    Returns:
        models.Job: Job object that was created or updated.
    """
    db = next(get_db())

    if state == "CREATE" and data_product_id:
        job_in = schemas.job.JobCreate(
            name=f"{name}-process",
            data_product_id=data_product_id,
            state="PENDING",
            status="WAITING",
            start_time=datetime.now(),
        )
        job = crud.job.create_job(db, job_in)

    if state == "INPROGRESS" and job:
        crud.job.update(
            db, db_obj=job, obj_in=JobUpdate(state="STARTED", status="INPROGRESS")
        )

    if state == "ERROR" and job:
        crud.job.update(
            db,
            db_obj=job,
            obj_in=schemas.job.JobUpdate(
                state="COMPLETED", status="FAILED", end_time=datetime.now()
            ),
        )

    if state == "DONE" and job:
        crud.job.update(
            db,
            db_obj=job,
            obj_in=schemas.job.JobUpdate(
                state="COMPLETED", status="SUCCESS", end_time=datetime.now()
            ),
        )

    return job
