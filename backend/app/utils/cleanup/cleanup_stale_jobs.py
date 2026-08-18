import logging
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy import and_, not_, select
from sqlalchemy.orm import Session

from app import crud
from app.models import DataProduct, Flight, Job, RawData
from app.schemas.job import State, Status
from app.utils.cleanup.common import (
    get_data_dir,
    get_retention_cutoff,
    log_removal,
    log_s3_skip,
    new_stats,
    remove_static_dir,
)

logger = logging.getLogger(__name__)

# Jobs that record an upload. A stale one means the upload never finished, so
# the partial data product or raw data it created can be removed along with it.
UPLOAD_JOB_NAMES = {
    "upload-data-product": ("data product", "data_products"),
    "upload-raw-data": ("raw data", "raw_data"),
}


def get_stale_jobs(session: Session) -> List[Any]:
    """Find upload jobs that never succeeded and are past the retention window.

    A job that finished successfully is COMPLETED and SUCCESS together. Anything
    else is either still stuck (PENDING or STARTED long after it began) or
    finished as FAILED, and in both cases the upload it was running never
    produced usable data.

    Args:
        session (Session): Database session.

    Returns:
        List[Any]: Rows of (job id, name, data product id, raw data id).
    """
    stale_jobs_query = select(
        Job.id, Job.name, Job.data_product_id, Job.raw_data_id
    ).where(
        and_(
            Job.name.in_(list(UPLOAD_JOB_NAMES)),
            not_(and_(Job.state == State.COMPLETED, Job.status == Status.SUCCESS)),
            Job.start_time < get_retention_cutoff(),
        )
    )
    return list(session.execute(stale_jobs_query).all())


def has_successful_job(
    session: Session,
    data_product_id: Optional[UUID] = None,
    raw_data_id: Optional[UUID] = None,
) -> bool:
    """Check whether any job succeeded for a data product or raw data.

    A successful job means something finished using the record, so the stale
    upload job is not evidence that the record can be removed.

    Args:
        session (Session): Database session.
        data_product_id (Optional[UUID]): ID of data product to check.
        raw_data_id (Optional[UUID]): ID of raw data to check.

    Returns:
        bool: True if a successful job references the record.
    """
    if data_product_id is not None:
        owner_filter = Job.data_product_id == data_product_id
    else:
        owner_filter = Job.raw_data_id == raw_data_id
    successful_job_query = (
        select(Job.id).where(and_(owner_filter, Job.status == Status.SUCCESS)).limit(1)
    )
    return session.execute(successful_job_query).first() is not None


def plan_removal(session: Session, stale_job: Any) -> Dict[str, Any]:
    """Decide what to remove for a stale upload job.

    The job's data product or raw data is removed with the job, unless it looks
    like it is still in use. In that case only the job is left in place and
    reported as skipped, because removing usable data is not recoverable.

    Args:
        session (Session): Database session.
        stale_job (Any): Row of (job id, name, data product id, raw data id).

    Returns:
        Dict[str, Any]: Plan with an "action" of "remove_data", "remove_job",
            or "skip", plus the details needed to carry it out.
    """
    job_id, job_name, data_product_id, raw_data_id = stale_job
    item_type, data_dir = UPLOAD_JOB_NAMES[job_name]
    is_data_product = job_name == "upload-data-product"
    data_id = data_product_id if is_data_product else raw_data_id

    # a job with no upload record left to clean up, so only the job remains
    if data_id is None:
        return {"action": "remove_job", "job_id": job_id}

    model = DataProduct if is_data_product else RawData
    data_query = (
        select(
            model.s3_url,
            model.is_initial_processing_completed,
            Flight.id,
            Flight.project_id,
        )
        .join(Flight, Flight.id == model.flight_id)
        .where(model.id == data_id)
    )
    data = session.execute(data_query).first()
    if data is None:
        # the upload record is already gone, so only the job remains
        return {"action": "remove_job", "job_id": job_id}

    s3_url, is_initial_processing_completed, flight_id, project_id = data
    if s3_url is not None:
        log_s3_skip(item_type, data_id)
        return {"action": "skip", "job_id": job_id}

    owner = (
        {"data_product_id": data_id} if is_data_product else {"raw_data_id": data_id}
    )
    if is_initial_processing_completed or has_successful_job(session, **owner):
        logger.warning(
            "Skipping %s %s for stale job %s: it finished processing or has a "
            "successful job, so the upload it belongs to is still in use.",
            item_type,
            data_id,
            job_id,
        )
        return {"action": "skip", "job_id": job_id}

    return {
        "action": "remove_data",
        "job_id": job_id,
        "data_id": data_id,
        "item_type": item_type,
        "crud_obj": crud.data_product if is_data_product else crud.raw_data,
        "static_dir": get_data_dir(project_id, flight_id, data_dir, data_id),
    }


def cleanup_stale_jobs(db: Session, check_only: bool = False) -> Dict[str, Any]:
    """Remove upload jobs that never succeeded, and the data they left behind.

    Removing the data product or raw data also removes the job, because jobs
    cascade from the record they belong to.

    Args:
        db (Session): Database session.
        check_only (bool): If True, report what would be removed without
            removing static files or database records.

    Returns:
        Dict[str, Any]: Result record described by common.new_stats.
    """
    stats = new_stats()
    with db as session:
        plans = [
            plan_removal(session, stale_job) for stale_job in get_stale_jobs(session)
        ]

    removed_data_ids: Set[UUID] = set()
    for plan in plans:
        if plan["action"] == "skip":
            stats["items_skipped"] += 1
            continue
        # more than one stale job can point at the same upload, and the first
        # one removes it for all of them
        if plan.get("data_id") in removed_data_ids:
            continue
        try:
            if plan["action"] == "remove_job":
                if not check_only:
                    crud.job.remove(db, id=plan["job_id"])
                logger.info(
                    "%s job %s (no upload record to remove)",
                    "Would remove" if check_only else "Removed",
                    plan["job_id"],
                )
                stats["items_removed"] += 1
                stats["removed_ids"].add(plan["job_id"])
                continue

            dir_size = remove_static_dir(plan["static_dir"], check_only)
            if not check_only:
                plan["crud_obj"].remove(db, id=plan["data_id"])
            log_removal(
                plan["item_type"],
                plan["data_id"],
                plan["static_dir"],
                dir_size,
                check_only,
            )
            stats["items_removed"] += 1
            stats["space_freed_up"] += dir_size
            stats["removed_ids"].add(plan["data_id"])
            removed_data_ids.add(plan["data_id"])
        except Exception:
            logger.exception("Failed to clean up stale job %s", plan["job_id"])
            stats["failures"] += 1

    return stats
