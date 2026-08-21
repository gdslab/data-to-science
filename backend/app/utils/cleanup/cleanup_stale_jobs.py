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
    get_project_ids_with_s3_objects,
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


def plan_removal(
    session: Session,
    stale_job: Any,
    s3_project_ids: Set[UUID],
    skip_project_ids: Set[UUID],
    skip_flight_ids: Set[UUID],
    skip_data_ids: Set[UUID],
) -> Dict[str, Any]:
    """Decide what to remove for a stale upload job.

    The job's data product or raw data is removed with the job, unless it looks
    like it is still in use. In that case only the job is left in place and
    reported as skipped, because removing usable data is not recoverable.

    Deciding is kept separate from acting so the caller can report the record a
    plan protects once, even when several stale jobs point at the same upload.

    Args:
        session (Session): Database session.
        stale_job (Any): Row of (job id, name, data product id, raw data id).
        s3_project_ids (Set[UUID]): Projects held back because they still have
            data in S3.
        skip_project_ids (Set[UUID]): Projects already covered by an earlier
            category in this run.
        skip_flight_ids (Set[UUID]): Flights already covered by an earlier
            category in this run.
        skip_data_ids (Set[UUID]): Data products and raw data already covered by
            an earlier category in this run.

    Returns:
        Dict[str, Any]: Plan with an "action" of "remove_data", "remove_job",
            "skip", or "covered", plus the details needed to carry it out. A
            "skip" plan carries the "reason" the record is being kept, and a
            "covered" plan is left for the category that already counted it.
    """
    job_id, job_name, data_product_id, raw_data_id = stale_job
    item_type, data_dir = UPLOAD_JOB_NAMES[job_name]
    is_data_product = job_name == "upload-data-product"
    data_id = data_product_id if is_data_product else raw_data_id

    # a job with no upload record left to clean up, so only the job remains
    if data_id is None:
        return {"action": "remove_job", "job_id": job_id}

    if data_id in skip_data_ids:
        return {"action": "covered", "job_id": job_id, "data_id": data_id}

    model = DataProduct if is_data_product else RawData
    data_query = (
        select(
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

    is_initial_processing_completed, flight_id, project_id = data
    if project_id in skip_project_ids or flight_id in skip_flight_ids:
        return {"action": "covered", "job_id": job_id, "data_id": data_id}

    skip_plan = {
        "action": "skip",
        "job_id": job_id,
        "data_id": data_id,
        "item_type": item_type,
    }
    if project_id in s3_project_ids:
        return {**skip_plan, "reason": "s3"}

    owner = (
        {"data_product_id": data_id} if is_data_product else {"raw_data_id": data_id}
    )
    if is_initial_processing_completed or has_successful_job(session, **owner):
        return {**skip_plan, "reason": "in_use"}

    return {
        "action": "remove_data",
        "job_id": job_id,
        "data_id": data_id,
        "item_type": item_type,
        "crud_obj": crud.data_product if is_data_product else crud.raw_data,
        "static_dir": get_data_dir(project_id, flight_id, data_dir, data_id),
    }


def log_skip(plan: Dict[str, Any]) -> None:
    """Record why a stale job's upload record was left in place.

    Args:
        plan (Dict[str, Any]): A "skip" plan from plan_removal.
    """
    if plan["reason"] == "s3":
        log_s3_skip(plan["item_type"], plan["data_id"])
        return
    logger.warning(
        "Skipping %s %s for stale job %s: it finished processing or has a "
        "successful job, so the upload it belongs to is still in use.",
        plan["item_type"],
        plan["data_id"],
        plan["job_id"],
    )


def cleanup_stale_jobs(
    db: Session,
    check_only: bool = False,
    skip_project_ids: Optional[Set[UUID]] = None,
    skip_flight_ids: Optional[Set[UUID]] = None,
    skip_data_ids: Optional[Set[UUID]] = None,
    s3_project_ids: Optional[Set[UUID]] = None,
) -> Dict[str, Any]:
    """Remove upload jobs that never succeeded, and the data they left behind.

    Removing the data product or raw data also removes the job, because jobs
    cascade from the record they belong to. That cascade is also why the
    records an earlier category covered have to be passed in: in a real run
    their jobs are already gone by the time this category runs, so counting
    them here would make a dry run report more than the run that follows it.

    Args:
        db (Session): Database session.
        check_only (bool): If True, report what would be removed without
            removing static files or database records.
        skip_project_ids (Optional[Set[UUID]]): Projects already covered by
            cleanup_projects in this run.
        skip_flight_ids (Optional[Set[UUID]]): Flights already covered by
            cleanup_flights in this run.
        skip_data_ids (Optional[Set[UUID]]): Data products and raw data already
            covered by cleanup_data_products_and_raw_data in this run.
        s3_project_ids (Optional[Set[UUID]]): Projects held back because they
            still have data in S3, from common.get_project_ids_with_s3_objects.
            Looked up here when the caller has not already done so.

    Returns:
        Dict[str, Any]: Result record described by common.new_stats.
    """
    stats = new_stats()
    skip_project_ids = skip_project_ids or set()
    skip_flight_ids = skip_flight_ids or set()
    skip_data_ids = skip_data_ids or set()

    with db as session:
        project_ids_with_s3_objects = (
            get_project_ids_with_s3_objects(session)
            if s3_project_ids is None
            else s3_project_ids
        )
        plans = [
            plan_removal(
                session,
                stale_job,
                project_ids_with_s3_objects,
                skip_project_ids,
                skip_flight_ids,
                skip_data_ids,
            )
            for stale_job in get_stale_jobs(session)
        ]

    # more than one stale job can point at the same upload. The first plan
    # settles what happens to it, so the rest are neither acted on nor counted.
    # "removed_ids" holds the uploads removed, matching the other categories;
    # the jobs removed on their own are not recorded there, because no other
    # category can see a job.
    skipped_data_ids: Set[UUID] = set()
    for plan in plans:
        # an earlier category already counted this record, and in a real run
        # removing it took the job with it, so counting it here would make a
        # dry run report more than the run that follows it
        if plan["action"] == "covered":
            continue
        if plan["action"] == "skip":
            if plan["data_id"] in skipped_data_ids:
                continue
            skipped_data_ids.add(plan["data_id"])
            log_skip(plan)
            stats["items_skipped"] += 1
            continue
        if plan.get("data_id") in stats["removed_ids"]:
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
        except Exception:
            logger.exception("Failed to clean up stale job %s", plan["job_id"])
            stats["failures"] += 1

    return stats
