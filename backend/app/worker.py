import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path, PosixPath
from typing import TypedDict
from uuid import UUID

from celery.utils.log import get_task_logger

from app import crud, models, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.schemas.data_product import DataProduct, DataProductUpdate
from app.schemas.job import JobUpdate

from app.utils.ImageProcessor import ImageProcessor
from app.utils.Toolbox import Toolbox


logger = get_task_logger(__name__)


@celery_app.task(name="test_celery")
def test_celery(word: str) -> str:
    return f"test task return {word}"


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
        if os.path.exists(out_raster) and ip:
            default_symbology = ip.get_default_symbology()
            # update data product record with stac properties
            crud.data_product.update(
                db,
                db_obj=new_data_product,
                obj_in=DataProductUpdate(stac_properties=ip.stac_properties),
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
    geotiff_filepath: str,
    user_id: UUID,
    project_id: UUID,
    flight_id: UUID,
    job_id: UUID,
    dtype: str,
    data_product: DataProduct | None = None,
) -> None:
    db = next(get_db())

    job = crud.job.get(db, id=job_id)
    if not job:
        raise Exception

    if job.status == "WAITING":
        crud.job.update(
            db, db_obj=job, obj_in=JobUpdate(state="STARTED", status="INPROGRESS")
        )

    if not data_product:
        data_product = crud.data_product.create_with_flight(
            db,
            schemas.DataProductCreate(
                data_type=dtype,
                filepath=geotiff_filepath.replace("__temp", ""),
                original_filename=original_filename,
            ),
            flight_id=flight_id,
        )
        if not data_product:
            crud.job.update(
                db,
                db_obj=job,
                obj_in=JobUpdate(
                    state="COMPLETED", status="FAILED", end_time=datetime.now()
                ),
            )
            return None

    crud.job.update(db, db_obj=job, obj_in=JobUpdate(data_product_id=data_product.id))

    # create COG for uploaded GeoTIFF if necessary
    try:
        ip = ImageProcessor(geotiff_filepath)
        ip.run()
        default_symbology = ip.get_default_symbology()
    except Exception as e:
        logger.exception("Failed to process uploaded GeoTIFF")
        if os.path.exists(geotiff_filepath):
            os.remove(geotiff_filepath)
        crud.job.update(
            db,
            db_obj=job,
            obj_in=JobUpdate(
                state="COMPLETED", status="FAILED", end_time=datetime.now()
            ),
        )
        return None

    crud.data_product.update(
        db,
        db_obj=data_product,
        obj_in=DataProductUpdate(stac_properties=ip.stac_properties),
    )

    crud.user_style.create_with_data_product_and_user(
        db,
        obj_in=default_symbology,
        data_product_id=data_product.id,
        user_id=user_id,
    )

    crud.job.update(
        db,
        db_obj=job,
        obj_in=JobUpdate(state="COMPLETED", status="SUCCESS", end_time=datetime.now()),
    )

    return None


@celery_app.task(name="point_cloud_upload_task")
def process_point_cloud(
    original_filename: str,
    las_filepath: str,
    project_id: UUID,
    flight_id: UUID,
    job_id: UUID,
    dtype: str,
) -> None:
    db = next(get_db())

    job = crud.job.get(db, id=job_id)
    if not job:
        raise Exception

    crud.job.update(
        db, db_obj=job, obj_in=JobUpdate(state="STARTED", status="INPROGRESS")
    )

    copc_laz_filepath = str(
        Path(las_filepath).parent / (Path(las_filepath).stem + ".copc.laz")
    )

    data_product = crud.data_product.create_with_flight(
        db,
        schemas.DataProductCreate(
            data_type=dtype,
            filepath=copc_laz_filepath,
            original_filename=original_filename,
        ),
        flight_id=flight_id,
    )

    if not data_product:
        crud.job.update(
            db,
            db_obj=job,
            obj_in=JobUpdate(
                state="COMPLETED", status="FAILED", end_time=datetime.now()
            ),
        )
        return None

    crud.job.update(db, db_obj=job, obj_in=JobUpdate(data_product_id=data_product.id))

    # Convert to entwine format
    out_root_dir = Path(las_filepath).parent
    out_ept_dir = Path(las_filepath).stem

    try:
        result = subprocess.run(
            [
                "entwine",
                "build",
                "-i",
                las_filepath,
                "-o",
                os.path.join(out_root_dir, out_ept_dir),
            ],
            stdout=subprocess.PIPE,
            check=True,
        )
        result.check_returncode()
    except Exception as e:
        logger.exception("Failed to build EPT from uploaded point cloud")
        os.remove(las_filepath)
        crud.job.update(
            db,
            db_obj=job,
            obj_in=JobUpdate(
                state="COMPLETED", status="FAILED", end_time=datetime.now()
            ),
        )
        return None

    try:
        result = subprocess.run(
            [
                "untwine",
                "--single_file",
                "-i",
                las_filepath,
                "-o",
                copc_laz_filepath,
            ]
        )
        if os.path.exists(f"{copc_laz_filepath}_tmp"):
            shutil.rmtree(f"{copc_laz_filepath}_tmp")
    except Exception as e:
        logger.exception("Failed to build COPC from uploaded point cloud")
        os.remove(las_filepath)
        if os.path.exists(f"{copc_laz_filepath}_tmp"):
            shutil.rmtree(f"{copc_laz_filepath}_tmp")
        crud.job.update(
            db,
            db_obj=job,
            obj_in=JobUpdate(
                state="COMPLETED", status="FAILED", end_time=datetime.now()
            ),
        )
        return None

    crud.job.update(
        db,
        db_obj=job,
        obj_in=JobUpdate(state="COMPLETED", status="SUCCESS", end_time=datetime.now()),
    )

    os.remove(las_filepath)

    return None


def update_job_status(
    job: models.Job | None,
    state: str,
    data_product_id: UUID | None = None,
    name: str = "unknown",
) -> models.Job:
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
