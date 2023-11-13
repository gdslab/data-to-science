import os
import shutil
import subprocess
from datetime import datetime
from uuid import UUID

from celery.utils.log import get_task_logger

from app import crud, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.schemas.data_product import DataProductUpdate
from app.schemas.job import JobUpdate

from app.utils.ImageProcessor import ImageProcessor


logger = get_task_logger(__name__)


@celery_app.task(name="test_celery")
def test_celery(word: str) -> str:
    return f"test task return {word}"


@celery_app.task(name="geotiff_upload_task")
def process_geotiff(
    filename: str,
    out_path: str,
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

    data_product = crud.data_product.create_with_flight(
        db,
        schemas.DataProductCreate(
            data_type=dtype,
            filepath=out_path.replace("__temp", ""),
            original_filename=os.path.basename(filename),
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
        ip = ImageProcessor(out_path)
        ip.run()
    except Exception as e:
        logger.error(str)
        if os.path.exists(out_path):
            os.remove(out_path)
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

    crud.job.update(
        db,
        db_obj=job,
        obj_in=JobUpdate(state="COMPLETED", status="SUCCESS", end_time=datetime.now()),
    )

    return None


@celery_app.task(name="point_cloud_upload_task")
def process_point_cloud(
    filename: str,
    out_path: str,
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

    data_product = crud.data_product.create_with_flight(
        db,
        schemas.DataProductCreate(
            data_type=dtype,
            filepath=out_path,
            original_filename=os.path.basename(filename),
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
    out_root_dir = os.path.dirname(out_path)
    out_ept_dir = os.path.basename(os.path.splitext(out_path.replace("__temp", ""))[0])

    try:
        result = subprocess.run(
            [
                "entwine",
                "build",
                "-i",
                out_path,
                "-o",
                os.path.join(out_root_dir, out_ept_dir),
            ],
            stdout=subprocess.PIPE,
            check=True,
        )
        result.check_returncode()
        shutil.make_archive(
            os.path.join(out_root_dir, out_ept_dir),
            "zip",
            os.path.join(out_root_dir, out_ept_dir),
        )
    except Exception as e:
        logger.error(str(e))
        os.remove(out_path)
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

    os.remove(out_path)

    return None
