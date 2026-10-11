import logging
from typing import Any, Dict, Optional, Sequence, Set
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app import crud
from app.models import DataProduct, Flight, RawData
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


def get_deactivated_data_query(model: Any) -> Select:
    """Build query for deactivated data products or raw data.

    The flight is joined so the static directory can be constructed without
    loading the records themselves.

    Args:
        model (Any): DataProduct or RawData model.

    Returns:
        Select: Query returning (id, flight id, project id) rows.
    """
    return (
        select(model.id, Flight.id, Flight.project_id)
        .join(Flight, Flight.id == model.flight_id)
        .where(
            and_(
                model.is_active.is_(False),
                model.deactivated_at < get_retention_cutoff(),
            )
        )
    )


def remove_deactivated_data(
    db: Session,
    deactivated_data: Sequence[Any],
    crud_obj: Any,
    item_type: str,
    data_dir: str,
    stats: Dict[str, Any],
    check_only: bool,
    skip_project_ids: Set[UUID],
    skip_flight_ids: Set[UUID],
    s3_project_ids: Set[UUID],
) -> None:
    """Remove static directories and database records for deactivated data.

    Args:
        db (Session): Database session.
        deactivated_data (Sequence[Any]): Rows of (id, flight id, project id)
            from get_deactivated_data_query.
        crud_obj (Any): CRUD object used to remove the database records.
        item_type (str): Type of record being removed, used in log messages.
        data_dir (str): Folder containing data (e.g., "data_products").
        stats (Dict[str, Any]): Result record updated in place.
        check_only (bool): If True, nothing is removed.
        skip_project_ids (Set[UUID]): Projects already covered by this run.
        skip_flight_ids (Set[UUID]): Flights already covered by this run.
        s3_project_ids (Set[UUID]): Projects held back because they still have
            data in S3.
    """
    for data_id, flight_id, project_id in deactivated_data:
        if project_id in skip_project_ids or flight_id in skip_flight_ids:
            continue
        # the hold covers every record in the project, not only the records
        # holding an s3_url, so the project stays recoverable as a whole
        if project_id in s3_project_ids:
            log_s3_skip(item_type, data_id)
            stats["items_skipped"] += 1
            continue
        try:
            static_dir = get_data_dir(project_id, flight_id, data_dir, data_id)
            dir_size = remove_static_dir(static_dir, check_only)
            if not check_only:
                crud_obj.remove(db, id=data_id)
            log_removal(item_type, data_id, static_dir, dir_size, check_only)
            stats["items_removed"] += 1
            stats["space_freed_up"] += dir_size
            stats["removed_ids"].add(data_id)
        except Exception:
            logger.exception("Failed to remove %s %s", item_type, data_id)
            stats["failures"] += 1


def cleanup_data_products_and_raw_data(
    db: Session,
    check_only: bool = False,
    skip_project_ids: Optional[Set[UUID]] = None,
    skip_flight_ids: Optional[Set[UUID]] = None,
    s3_project_ids: Optional[Set[UUID]] = None,
) -> Dict[str, Any]:
    """Remove data products and raw data deactivated longer ago than the
    retention window.

    Every record in a project that still has data copied to S3 is skipped,
    including the records holding no S3 objects themselves. See
    common.get_project_ids_with_s3_objects for why the hold covers the whole
    project.

    Args:
        db (Session): Database session.
        check_only (bool): If True, report what would be removed without
            removing static files or database records.
        skip_project_ids (Optional[Set[UUID]]): Projects already covered by
            cleanup_projects in this run.
        skip_flight_ids (Optional[Set[UUID]]): Flights already covered by
            cleanup_flights in this run.
        s3_project_ids (Optional[Set[UUID]]): Projects held back because they
            still have data in S3, from common.get_project_ids_with_s3_objects.
            Looked up here when the caller has not already done so.

    Returns:
        Dict[str, Any]: Result record described by common.new_stats.
    """
    stats = new_stats()
    skip_project_ids = skip_project_ids or set()
    skip_flight_ids = skip_flight_ids or set()

    with db as session:
        deactivated_data_products = session.execute(
            get_deactivated_data_query(DataProduct)
        ).all()
        deactivated_raw_data = session.execute(
            get_deactivated_data_query(RawData)
        ).all()
        project_ids_with_s3_objects = (
            get_project_ids_with_s3_objects(session)
            if s3_project_ids is None
            else s3_project_ids
        )

    remove_deactivated_data(
        db,
        deactivated_data_products,
        crud.data_product,
        "data product",
        "data_products",
        stats,
        check_only,
        skip_project_ids,
        skip_flight_ids,
        project_ids_with_s3_objects,
    )
    remove_deactivated_data(
        db,
        deactivated_raw_data,
        crud.raw_data,
        "raw data",
        "raw_data",
        stats,
        check_only,
        skip_project_ids,
        skip_flight_ids,
        project_ids_with_s3_objects,
    )

    return stats
