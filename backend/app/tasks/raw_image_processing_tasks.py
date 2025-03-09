import asyncio
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from uuid import UUID

from celery.utils.log import get_task_logger

from app import crud, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.security import get_token_hash
from app.utils.job_manager import JobManager
from app.schemas.job import Status
from app.utils.job_manager import JobManager
from app.utils.RpcClient import RpcClient
from app.utils.unique_id import generate_unique_id


logger = get_task_logger(__name__)


def cleanup_on_external(destination_path: str) -> None:
    try:
        os.remove(destination_path)
    except Exception:
        logger.exception(
            f"Error while cleaning up external storage: {destination_path}"
        )


async def async_transfer(
    external_storage_dir: str,
    storage_path: str,
    original_filename: str,
    project_id: UUID,
    flight_id: UUID,
    raw_data_id: UUID,
    user_id: UUID,
    job_id: UUID,
    ip_settings: Dict,
) -> Tuple[UUID, Optional[str]]:
    logger.info(f"Transferring raw data to external storage for job {job_id}")

    # Create database session
    db = next(get_db())

    try:
        # Start current job
        job = JobManager(job_id=job_id)
        job.start()

        # Construct fullpath for raw data file on external storage
        destination_dir = os.path.join(external_storage_dir, "raw_data")
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        # Create unique id for raw data and copy file to external storage
        raw_data_identifier = generate_unique_id()
        destination_path = os.path.join(destination_dir, f"{raw_data_identifier}.zip")

        # Transfer raw data to external storage
        process = await asyncio.create_subprocess_exec(
            "rsync",
            "-avz",
            storage_path,
            destination_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        _, stderr = await process.communicate()

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
            os.path.join(destination_dir, raw_data_identifier + ".info"), "w"
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

        if process.returncode != 0:
            job.update(status=Status.FAILED)
            logger.error(f"Transfer failed for job {job_id}")
            cleanup_on_external(destination_path)
            raise Exception(f"Transfer failed: {stderr.decode()}")

    except Exception:
        logger.exception("Transfer failed for job {job_id}")
        job.update(status=Status.FAILED)
        cleanup_on_external(destination_path)
        return job_id, None

    logger.info(f"Transfer successful for job {job_id}")

    return job_id, raw_data_identifier


@celery_app.task(name="transfer_raw_data_task")
def transfer_raw_data(
    external_storage_dir: str,
    storage_path: str,
    original_filename: str,
    project_id: UUID,
    flight_id: UUID,
    raw_data_id: UUID,
    user_id: UUID,
    job_id: UUID,
    ip_settings: Dict,
) -> Tuple[UUID, str]:
    job_id, raw_data_identifier = asyncio.run(
        async_transfer(
            external_storage_dir,
            storage_path,
            original_filename,
            project_id,
            flight_id,
            raw_data_id,
            user_id,
            job_id,
            ip_settings,
        )
    )

    if not raw_data_identifier:
        job = JobManager(job_id=job_id)
        job.update(status=Status.FAILED)
        logger.error(f"Error while transferring raw data for job {job_id}")
        raise Exception("Error while transferring raw data")

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
