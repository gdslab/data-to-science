import json
import os
import tarfile
import secrets
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, TypedDict
from uuid import UUID

import geopandas as gpd
import pika
import rasterio
from celery.utils.log import get_task_logger
from fastapi.encoders import jsonable_encoder
from geojson_pydantic import Feature, FeatureCollection, Polygon
from rasterstats import zonal_stats
from sqlalchemy.exc import IntegrityError

from app import crud, models, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.security import get_token_hash
from app.schemas.data_product import DataProduct, DataProductUpdate
from app.schemas.data_product_metadata import (
    ZonalFeature,
    ZonalFeatureCollection,
    ZonalStatistics,
    ZonalStatisticsProps,
)
from app.schemas.job import JobUpdate
from app.schemas.raw_data import ImageProcessingQueryParams
from app.utils import gen_preview_from_pointcloud
from app.utils.ImageProcessor import ImageProcessor
from app.utils.rabbitmq import get_pika_connection
from app.utils.RpcClient import RpcClient
from app.utils.TarProcessor import TarProcessor
from app.utils.Toolbox import Toolbox
from app.utils.unique_id import generate_unique_id


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
                    filepath=out_raster,
                    stac_properties=ip.stac_properties,
                    is_initial_processing_completed=True,
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
    try:
        crud.data_product.update(
            db,
            db_obj=data_product,
            obj_in=DataProductUpdate(
                filepath=str(out_raster),
                stac_properties=jsonable_encoder(ip.stac_properties),
            ),
        )
    except Exception as e:
        if os.path.exists(in_raster.parents[1]):
            shutil.rmtree(in_raster.parents[1])
        update_job_status(job, state="ERROR")
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
    update_job_status(job, state="DONE")

    # remove the uploaded geotiff from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception(
            f"Unable to cleanup data product upload on tusd server: {data_product_id}"
        )
    finally:
        return None


@celery_app.task(name="point_cloud_preview_image_task")
def create_point_cloud_preview_image(in_las: str) -> None:
    """Celery task for creating a preview image for a point cloud.

    Args:
        in_las (str): Path to point cloud.
    """
    # create preview image with uploaded point cloud
    try:
        in_las_pth = Path(in_las)
        if in_las_pth.name.endswith(".copc.laz"):
            preview_out_path = in_las_pth.parents[0] / in_las_pth.name.replace(
                ".copc.laz", ".png"
            )
        else:
            preview_out_path = (
                in_las_pth.parents[0] / in_las_pth.with_suffix(".png").name
            )
        gen_preview_from_pointcloud.create_preview_image(
            input_las_path=in_las_pth,
            preview_out_path=preview_out_path,
        )
    except Exception as e:
        logger.exception("Unable to generate preview image for uploaded point cloud")
        # if this file is present the preview image generation will be skipped next time
        with open(Path(in_las_pth).parent / "preview_failed", "w") as preview:
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
        obj_in=DataProductUpdate(
            filepath=str(copc_laz_filepath), is_initial_processing_completed=True
        ),
    )

    # update job to indicate process finished
    update_job_status(job, state="DONE")

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


@celery_app.task(name="raw_data_upload_task")
def process_raw_data(
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
    # get database session
    db = next(get_db())
    # retrieve job associated with this task
    job = crud.job.get(db, id=job_id)
    if not job:
        logger.error(f"Unable to find job for processing raw data: {raw_data_id}")
        return None
    # retrieve raw data associated with this task
    raw_data = crud.raw_data.get(db, id=raw_data_id)
    if not raw_data:
        logger.error(f"Unable to find raw data record: {raw_data_id}")
        update_job_status(job, state="ERROR")
        return None
    update_job_status(job, state="INPROGRESS")
    try:
        # copy uploaded raw data to static files and update record
        shutil.copyfile(storage_path, destination_filepath)

        # add filepath to raw data object
        crud.raw_data.update(
            db,
            db_obj=raw_data,
            obj_in=schemas.RawDataUpdate(
                filepath=str(destination_filepath), is_initial_processing_completed=True
            ),
        )
    except Exception:
        logger.exception(f"Failed to process uploaded raw data: {raw_data_id}")
        # clean up any files
        if os.path.exists(destination_filepath):
            os.remove(destination_filepath)
        update_job_status(job, state="ERROR")
        return None

    update_job_status(job, state="DONE")

    # remove raw data from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception(
            f"Unable to cleanup raw data upload on tusd server: {raw_data_id}"
        )
    finally:
        return None


@celery_app.task(name="raw_data_image_processing_task")
def run_raw_data_image_processing(
    external_storage_dir: str,
    storage_path: str,
    original_filename: str,
    project_id: UUID,
    flight_id: UUID,
    raw_data_id: UUID,
    user_id: UUID,
    job_id: UUID,
    ip_settings: Dict,
) -> None:
    """Starts job on external server to process raw data.

    Args:
        external_storage_dir (str): Root directory of external storage.
        storage_path (str): Current location of raw data zip file.
        original_filename (str): Raw data's original filename.
        project_id (UUID): ID for project associated with raw data.
        flight_id (UUID): ID for flight associated with raw data.
        raw_data_id (UUID): ID for raw data.
        user_id (UUID): ID for user associated with raw data processing request.
        ip_settings (ImageProcessingQueryParams): User defined processing settings.

    Raises:
        HTTPException: Raised if copying raw data to external storage fails.
        HTTPException: Raised if unable to start job on remote server.
    """
    # get database session
    db = next(get_db())
    # retrieve job associated with this task
    job = crud.job.get(db, id=job_id)
    if not job:
        logger.error(f"Unable to find job for processing raw data: {raw_data_id}")
        return None
    # update job status to indicate process has started
    update_job_status(job, state="INPROGRESS")
    try:
        # destination for raw data zips
        external_raw_data_dir = os.path.join(external_storage_dir, "raw_data")
        if not os.path.exists(external_raw_data_dir):
            os.makedirs(external_raw_data_dir)

        # create unique id for raw data and copy file to external storage
        raw_data_identifier = generate_unique_id()
        shutil.copyfile(
            storage_path,
            os.path.join(external_raw_data_dir, raw_data_identifier + ".zip"),
        )

        # create one time token
        token = secrets.token_urlsafe()
        crud.user.create_single_use_token(
            db,
            obj_in=schemas.SingleUseTokenCreate(
                token=get_token_hash(token, salt="rawdata")
            ),
            user_id=user_id,
        )

        with open(
            os.path.join(external_raw_data_dir, raw_data_identifier + ".info"), "w"
        ) as info_file:
            raw_data_meta = {
                "callback_url": f"{settings.API_DOMAIN}{settings.API_V1_STR}/projects/{project_id}/flights/{flight_id}/data_products/create_from_ext_storage",
                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "flight_id": str(flight_id),
                "original_filename": original_filename,
                "project_id": str(project_id),
                "raw_data_id": str(raw_data_id),
                "root_dir": external_storage_dir,
                "token": token,
                "user_id": str(user_id),
                "job_id": str(job.id),
                "settings": ip_settings,
            }
            info_file.write(json.dumps(raw_data_meta))
    except Exception:
        logger.exception(
            "Error while moving raw data to external storage and creating metadata"
        )
        # update job
        update_job_status(job, state="ERROR")
        return None

    rpc_client = None
    try:
        # publish message to external server
        rpc_client = RpcClient(routing_key="raw-data-start-process-queue")
        batch_id = rpc_client.call(raw_data_identifier)

        # if no batch id returned, update job state as failed
        if not batch_id:
            raise ValueError("Missing batch ID")

        logger.info(f"Batch_ID: {batch_id}")

        update_job_status(job, state="INPROGRESS", extra={"batch_id": batch_id})
    except Exception:
        logger.exception("Error while publishing to RabbitMQ channel")
        # update job
        update_job_status(job, state="ERROR")
    finally:
        if isinstance(rpc_client, RpcClient):
            rpc_client.connection.close()

    return None


@celery_app.task(name="indoor_project_data_upload_task")
def process_indoor_project_data(
    indoor_project_data_id: UUID,
    storage_path: str,
    destination_filepath: str,
    job_id: UUID,
    indoor_project_id: UUID,
    uploader_id: UUID,
) -> None:
    """Celery task for copying uploaded indoor project data (.xls, .xlsx, or .tar)
    to static files location.

    Args:
        indoor_project_data_id (UUID): ID for indoor project data record.
        storage_path (Path): Location of indoor project data on tusd server.
        destination_filepath (Path): Destination in static files directory for data.
        job_id (UUID): ID for job tracking task progress.
        indoor_project_id (UUID): ID for indoor project associated with indoor project data.
        uploader_id (UUID): ID for user associated with indoor project data upload.
    """
    # get database session
    db = next(get_db())
    # retrieve job associated with this task
    job = crud.job.get(db, id=job_id)
    if not job:
        logger.error(
            f"Unable to find job for processing indoor project data: {indoor_project_data_id}"
        )
        return None

    logger.info(f"Running indoor project data processing task - JOB_ID: {job.id}")

    # retrieve indoor project data associated with this task
    indoor_project_data = crud.indoor_project_data.get(db, id=indoor_project_data_id)
    if not indoor_project_data:
        logger.error(f"Unable to find indoor project data: {indoor_project_data_id}")
        update_job_status(job, state="ERROR")
        return None
    update_job_status(job, state="INPROGRESS")
    try:
        logger.info("Copying uploaded indoor project data from tusd to user volume...")

        # copy uploaded indoor project data to static files and update filepath
        shutil.copyfile(storage_path, destination_filepath)

        # add filepath to indoor project data
        indoor_project_data_update_in = (
            schemas.indoor_project_data.IndoorProjectDataUpdate(
                file_path=str(destination_filepath)
            )
        )
        indoor_project_data_updated = crud.indoor_project_data.update(
            db, db_obj=indoor_project_data, obj_in=indoor_project_data_update_in
        )
        logger.info(indoor_project_data_updated)

        logger.info(
            "Copying uploaded indoor project data from tusd to user volume...Done!"
        )
    except Exception:
        logger.exception(
            f"Failed to process uploaded indoor data: {indoor_project_data_id}"
        )
        # clean up any files
        if os.path.exists(destination_filepath):
            os.remove(destination_filepath)
        update_job_status(job, state="ERROR")
        return None

    # extract contents if this is a tar archive
    if tarfile.is_tarfile(destination_filepath):
        logger.info("Extracting indoor project data tar archive contents...")
        try:
            tar_processor = TarProcessor(tar_file_path=destination_filepath)
            tar_processor.extract()
            tar_dir_structure = tar_processor.get_directory_structure()
            # update indoor project data with tar directory structure
            indoor_project_data_update_in = (
                schemas.indoor_project_data.IndoorProjectDataUpdate(
                    directory_structure=tar_dir_structure
                )
            )
            crud.indoor_project_data.update(
                db,
                db_obj=indoor_project_data_updated,
                obj_in=indoor_project_data_update_in,
            )
        except Exception as e:
            logger.exception(f"Failed to extract tar archive at {destination_filepath}")
            # clean up any files
            if os.path.exists(destination_filepath):
                os.remove(destination_filepath)
            update_job_status(job, state="ERROR")
            return None

        # remove tar after extraction finishes
        tar_processor.remove()

        logger.info("Extracting indoor project data tar archive contents...Done!")

    update_job_status(job, state="DONE")

    # remove indoor project data from tusd
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if os.path.exists(f"{storage_path}.info"):
            os.remove(f"{storage_path}.info")
    except Exception:
        logger.exception(
            f"Unable to cleanup indoor project data upload on tusd server: {indoor_project_data_id}"
        )
    finally:
        return None


@celery_app.task(name="zonal_statistics_task")
def generate_zonal_statistics(
    input_raster: str, feature_collection: dict
) -> List[ZonalStatisticsProps]:
    with rasterio.open(input_raster) as src:
        # convert feature collection to dataframe and update crs to match src crs
        zones = gpd.GeoDataFrame.from_features(
            feature_collection["features"], crs="EPSG:4326"
        )
        zones = zones.to_crs(src.crs)
        minx, miny, maxx, maxy = zones.total_bounds
        # affine transformation
        affine = src.transform
        # create window for total bounding box of all zones in zone_feature
        window = rasterio.windows.from_bounds(minx, miny, maxx, maxy, affine)
        window_affine = rasterio.windows.transform(window, src.transform)
        # read first band contained within window into array
        data = src.read(1, window=window)
        # required zonal statistics
        required_stats = "count min max mean median std"
        # get stats for zone
        stats = zonal_stats(zones, data, affine=window_affine, stats=required_stats)

    return stats


@celery_app.task(name="zonal_statistics_bulk_task")
def generate_zonal_statistics_bulk(
    input_raster: str, data_product_id: UUID, feature_collection: dict
) -> List[ZonalStatisticsProps]:
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
        return []

    try:
        # deserialize feature collection
        features = ZonalFeatureCollection(**feature_collection).features
        # create metadata record for each zone
        for index, zonal_stats in enumerate(all_zonal_stats):
            metadata_in = schemas.DataProductMetadataCreate(
                category="zonal",
                properties={"stats": zonal_stats},
                vector_layer_id=features[index].properties["id"],
            )
            try:
                crud.data_product_metadata.create_with_data_product(
                    db, obj_in=metadata_in, data_product_id=data_product_id
                )
            except IntegrityError:
                # update existing metadata
                existing_metadata = crud.data_product_metadata.get_by_data_product(
                    db,
                    category="zonal",
                    data_product_id=data_product_id,
                    vector_layer_id=features[index].properties["id"],
                )
                if len(existing_metadata) == 1:
                    crud.data_product_metadata.update(
                        db,
                        db_obj=existing_metadata[0],
                        obj_in=schemas.DataProductMetadataUpdate(
                            properties={"stats": zonal_stats}
                        ),
                    )
                else:
                    logger.exception("Unable to save zonal statistics")
                    update_job_status(job=job, state="ERROR")
                    return []
    except Exception:
        logger.exception("Unable to save zonal statistics")
        update_job_status(job=job, state="ERROR")
        return []

    # update job to indicate process finished
    update_job_status(job, state="DONE")

    return all_zonal_stats


def update_job_status(
    job: models.Job | None,
    state: str,
    data_product_id: UUID | None = None,
    raw_data_id: UUID | None = None,
    name: str = "unknown",
    extra: dict | None = None,
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
        if extra:
            crud.job.update(
                db,
                db_obj=job,
                obj_in=JobUpdate(state="STARTED", status="INPROGRESS", extra=extra),
            )
        else:
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
