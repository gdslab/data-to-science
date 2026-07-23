import asyncio
import json
import os
import secrets
import shutil
from datetime import datetime, timezone
from typing import Literal, Tuple, Union
from uuid import UUID

from celery import Task
from celery.utils.log import get_task_logger

from app import crud, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.security import get_token_hash
from app.schemas.image_processing_backend import ImageProcessingBackend
from app.schemas.job import Status
from app.schemas.raw_data import MetashapeQueryParams, ODMQueryParams
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


def fail_job(job: JobManager, detail: str) -> None:
    """Mark job as failed with a user-facing reason, preserving existing extra.

    Args:
        job (JobManager): Job manager for the job to mark as failed.
        detail (str): Reason for the failure shown in the processing history.
    """
    extra = dict(job.job.extra) if job.job and job.job.extra else {}
    extra["detail"] = detail
    job.update(status=Status.FAILED, extra=extra)


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
    backend: Literal["metashape", "odm"],
    ip_settings: Union[MetashapeQueryParams, ODMQueryParams],
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
        backend (Literal["metashape", "odm"]): Backend to use.
        ip_settings (Union[MetashapeQueryParams, ODMQueryParams]): Image processing settings.

    Raises:
        Exception: Raised if transfer fails.

    Returns:
        Tuple[UUID, Optional[str]]: Job ID and generated raw data identifier.
    """
    logger.info(f"Transferring raw data to external storage for job {job_id}")
    logger.info(f"backend: {backend}")
    # Create database session and start job
    db = next(get_db())
    job = JobManager(job_id=job_id)
    job.start()

    # Construct destination directory and path
    destination_dir = os.path.join(external_storage_dir, "raw_data")
    try:
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
        raw_data_identifier = generate_unique_id()
        destination_path = os.path.join(destination_dir, f"{raw_data_identifier}.zip")
    except Exception:
        logger.exception(f"Unable to access external storage for job {job_id}")
        fail_job(
            job,
            "The processing service is currently unavailable. Please try again later.",
        )
        raise

    # Attempt to transfer raw data with up to 3 retries
    try:
        asyncio.run(async_transfer(storage_path, destination_path, raw_data_identifier))
    except Exception as exc:
        logger.exception(f"Error while transferring raw data for job {job_id}")
        # Check if we've reached max retries
        if self.request.retries >= self.max_retries:
            logger.error(f"Max retries reached for job {job_id}")
            fail_job(
                job,
                "Data could not be sent to the processing service. Please try again later.",
            )
            cleanup_on_external(destination_dir, raw_data_identifier)
            raise exc
        else:
            logger.info(f"Retrying transfer for job {job_id}")
            raise self.retry(exc=exc)

    # Create one time token and write metadata to info file on remote server
    try:
        token = secrets.token_urlsafe()
        crud.user.create_single_use_token(
            db,
            obj_in=schemas.SingleUseTokenCreate(
                token=get_token_hash(token, salt="rawdata")
            ),
            user_id=user_id,
        )

        info_path = os.path.join(destination_dir, raw_data_identifier + ".info")
        with open(info_path, "w") as info_file:
            raw_data_meta = {
                "callback_url": (
                    f"{settings.API_DOMAIN}{settings.API_V1_STR}/projects/"
                    f"{project_id}/flights/{flight_id}/data_products/"
                    "create_from_ext_storage"
                ),
                "progress_callback_url": (
                    f"{settings.API_DOMAIN}{settings.API_V1_STR}/projects/"
                    f"{project_id}/flights/{flight_id}/raw_data/"
                    f"{raw_data_id}/progress_update"
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
                "backend": backend,
                "settings": ip_settings,
            }
            info_file.write(json.dumps(raw_data_meta))
    except Exception:
        logger.exception("Error while writing metadata to info file")
        fail_job(
            job, "Processing could not be started. Please try again later."
        )
        cleanup_on_external(destination_dir, raw_data_identifier)
        # re-raise so the chain stops and the job is not resumed
        raise

    logger.info(f"Transfer successful for job {job_id}")

    return job_id, raw_data_identifier


@celery_app.task(name="start_raw_data_processing_task")
def start_raw_data_processing(task_data: Tuple[UUID, str]) -> None:
    """Starts job on external server to process raw data.

    Args:
        job_id (UUID): Unique identifier for job.
        raw_data_identifier (str): Unique identifier for raw data.

    Raises:
        HTTPException: Raised if unable to start job on remote server.
    """
    job_id, raw_data_identifier = task_data

    # Get job manager for current job; if the job cannot be found there is
    # nothing to mark as failed
    job = JobManager(job_id=job_id)

    try:
        # publish message to external server
        with RpcClient(routing_key="raw-data-start-process-queue") as rpc_client:
            reply = rpc_client.call(raw_data_identifier)
    except Exception:
        logger.exception("Error while publishing to RabbitMQ channel")
        fail_job(
            job,
            "The processing service did not respond. Please try again later.",
        )
        return

    if reply and reply.startswith("Error:"):
        # remote reported a hard error while accepting the request
        logger.error(f"Processing service rejected job {job_id}: {reply}")
        fail_job(
            job,
            "The processing service reported an error. Please try again later.",
        )
        return

    if not reply:
        # A batch id is assigned by the remote only once its backend (e.g.
        # Metashape) creates a project, which may be after this ack. The job
        # is already INPROGRESS; progress arrives via progress_update pushes.
        logger.info(f"Batch ID not yet available for job {job_id}; continuing")
        return

    logger.info(f"Batch_ID: {reply}")

    # merge batch id into existing extra to preserve stored settings
    existing_extra = dict(job.job.extra) if job.job and job.job.extra else {}
    existing_extra["batch_id"] = reply
    job.update(status=Status.INPROGRESS, extra=existing_extra)
