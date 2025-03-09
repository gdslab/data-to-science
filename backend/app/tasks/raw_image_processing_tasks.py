import json
import os
import secrets
import shutil
from datetime import datetime, timezone
from typing import Dict
from uuid import UUID

from celery.utils.log import get_task_logger

from app import crud, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.security import get_token_hash
from app.tasks.job_manager import JobManager
from app.schemas.job import Status
from app.utils.RpcClient import RpcClient
from app.utils.unique_id import generate_unique_id


logger = get_task_logger(__name__)


@celery_app.task(name="transfer_raw_data_task")
async def transfer_raw_data(job_id: UUID) -> None:
    logger.info("Raw data file transfer task started.")

    # Get database session
    db = next(get_db())

    # Look up job in database
    job = crud.job.get(db, id=job_id)

    # If job not found, log error and return
    if not job:
        logger.error(f"Job with ID {job_id} not found.")
        return

    # Update job state


@celery_app.task(name="process_raw_data_task")
def process_raw_data(
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
    try:
        job = JobManager(job_id=job_id)
    except ValueError:
        logger.error("Could not find job in DB for upload process")
        return None

    # update job status to indicate process has started
    job.start()

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
                "callback_url": (
                    f"{settings.API_DOMAIN}{settings.API_V1_STR}/projects/"
                    f"{project_id}/flights/{flight_id}/data_products/"
                    "create_from_ext_storage"
                ),
                "created_at": datetime.now(tz=timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),
                "flight_id": str(flight_id),
                "original_filename": original_filename,
                "project_id": str(project_id),
                "raw_data_id": str(raw_data_id),
                "root_dir": external_storage_dir,
                "token": token,
                "user_id": str(user_id),
                "job_id": str(job_id),
                "settings": ip_settings,
            }
            info_file.write(json.dumps(raw_data_meta))
    except Exception:
        logger.exception(
            "Error while moving raw data to external storage and creating metadata"
        )
        # update job
        job.update(status=Status.FAILED)
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

        job.update(status=Status.INPROGRESS, extra={"batch_id": batch_id})
    except Exception:
        logger.exception("Error while publishing to RabbitMQ channel")
        # update job
        job.update(status=Status.FAILED)
    finally:
        if isinstance(rpc_client, RpcClient):
            rpc_client.connection.close()

    return None
