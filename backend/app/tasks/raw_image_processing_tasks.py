import asyncio
import json
import os
import secrets
import shutil
from datetime import datetime, timezone
from typing import Dict, Tuple
from uuid import UUID

from celery import Task
from celery.utils.log import get_task_logger

from app import crud, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.security import get_token_hash
from app.schemas.job import Status
from app.utils.job_manager import JobManager
from app.utils.RpcClient import RpcClient
from app.utils.unique_id import generate_unique_id


logger = get_task_logger(__name__)


def cleanup_on_external(destination_dir: str, raw_data_identifier: str) -> None:
    """Remove file from external storage.

    Args:
        destination_dir (str): Destination directory.
        raw_data_identifier (str): Unique identifier for raw data.
    """
    raw_data_zip = os.path.join(destination_dir, f"{raw_data_identifier}.zip")
    raw_data_info = os.path.join(destination_dir, f"{raw_data_identifier}.info")
    raw_data_partial_dir = os.path.join(
        destination_dir, f".rsync-partial-{raw_data_identifier}"
    )

    if os.path.exists(raw_data_zip):
        try:
            os.remove(raw_data_zip)
        except Exception:
            logger.exception(
                f"Error while cleaning up external storage: {raw_data_zip}"
            )

    if os.path.exists(raw_data_info):
        try:
            os.remove(raw_data_info)
        except Exception:
            logger.exception(
                f"Error while cleaning up external storage: {raw_data_info}"
            )

    if os.path.exists(raw_data_partial_dir):
        try:
            shutil.rmtree(raw_data_partial_dir)
        except Exception:
            logger.exception(
                f"Error while cleaning up external storage: {raw_data_partial_dir}"
            )


async def async_transfer(
    source_path: str,
    destination_path: str,
    raw_data_identifier: str,
) -> None:
    """Transfer raw data to external storage using rsync.

    Args:
        source_path (str): Path to raw data on local server.
        destination_path (str): Destination for raw data on remote server.
        raw_data_identifier (str): Unique identifier for raw data.
    """
    process = await asyncio.create_subprocess_exec(
        "rsync",
        "-az",
        "--partial",  # keep partially transferred files
        f"--partial-dir=.rsync-partial-{raw_data_identifier}",
        source_path,
        destination_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    _, stderr = await process.communicate()

    if process.returncode != 0:
        raise Exception(f"Transfer failed: {stderr.decode()}")


@celery_app.task(
    name="transfer_raw_data_task", bind=True, max_retries=3, default_retry_delay=60
)
def transfer_raw_data(
    self: Task,
    external_storage_dir: str,
    storage_path: str,
    original_filename: str,
    prj_name: str,
    project_id: UUID,
    flight_id: UUID,
    raw_data_id: UUID,
    user_id: UUID,
    job_id: UUID,
    ip_settings: Dict,
) -> Tuple[UUID, str]:
    """Transfer raw data to external storage using rsync.

    Args:
        self (Task): Celery task instance.
        external_storage_dir (str): External storage directory.
        storage_path (str): Raw data storage path.
        original_filename (str): Original filename of raw data.
        project_id (UUID): Project ID.
        flight_id (UUID): Flight ID.
        raw_data_id (UUID): Raw data ID.
        user_id (UUID): User ID.
        job_id (UUID): Job ID.
        ip_settings (Dict): Image processing settings.

    Raises:
        Exception: Raised if transfer fails.

    Returns:
        Tuple[UUID, Optional[str]]: Job ID and generated raw data identifier.
    """
    logger.info(f"Transferring raw data to external storage for job {job_id}")

    # Create database session and start job
    db = next(get_db())
    job = JobManager(job_id=job_id)
    job.start()

    # Construct destination directory and path
    destination_dir = os.path.join(external_storage_dir, "raw_data")
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    raw_data_identifier = generate_unique_id()
    destination_path = os.path.join(destination_dir, f"{raw_data_identifier}.zip")

    # Attempt to transfer raw data with up to 3 retries
    try:
        asyncio.run(async_transfer(storage_path, destination_path, raw_data_identifier))
    except Exception as exc:
        logger.exception(f"Error while transferring raw data for job {job_id}")
        # Check if we've reached max retries
        if self.request.retries >= self.max_retries:
            logger.error(f"Max retries reached for job {job_id}")
            job.update(status=Status.FAILED)
            cleanup_on_external(destination_dir, raw_data_identifier)
            raise exc
        else:
            logger.info(f"Retrying transfer for job {job_id}")
            raise self.retry(exc=exc)

    # Create one time token
    token = secrets.token_urlsafe()
    crud.user.create_single_use_token(
        db,
        obj_in=schemas.SingleUseTokenCreate(
            token=get_token_hash(token, salt="rawdata")
        ),
        user_id=user_id,
    )

    # Write metadata to info file on remote server
    try:
        info_path = os.path.join(destination_dir, raw_data_identifier + ".info")
        with open(info_path, "w") as info_file:
            raw_data_meta = {
                "callback_url": (
                    f"{settings.API_DOMAIN}{settings.API_V1_STR}/projects/"
                    f"{project_id}/flights/{flight_id}/data_products/"
                    "create_from_ext_storage"
                ),
                "created_at": datetime.now(tz=timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),
                "prj_name": prj_name,
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
        logger.exception("Error while writing metadata to info file")
        job.update(status=Status.FAILED)
        cleanup_on_external(destination_dir, raw_data_identifier)

    logger.info(f"Transfer successful for job {job_id}")

    return job_id, raw_data_identifier


@celery_app.task(name="process_raw_data_task")
def process_raw_data(task_data: Tuple[UUID, str]) -> None:
    """Starts job on external server to process raw data.

    Args:
        job_id (UUID): Unique identifier for job.
        raw_data_identifier (str): Unique identifier for raw data.

    Raises:
        HTTPException: Raised if unable to start job on remote server.
    """
    job_id, raw_data_identifier = task_data

    try:
        # Get job manager for current job
        job = JobManager(job_id=job_id)

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
