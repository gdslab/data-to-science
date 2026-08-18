import logging
from typing import Any, Dict, Optional, Set
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import crud
from app.models import Flight
from app.utils.cleanup.common import (
    get_flight_dir,
    get_flight_ids_with_s3_objects,
    get_retention_cutoff,
    log_removal,
    log_s3_skip,
    new_stats,
    remove_static_dir,
)

logger = logging.getLogger(__name__)


def cleanup_flights(
    db: Session,
    check_only: bool = False,
    skip_project_ids: Optional[Set[UUID]] = None,
) -> Dict[str, Any]:
    """Remove flights deactivated longer ago than the retention window.

    Removing a flight removes its static directory and, through database
    cascades, its data products and raw data. Flights that still have data
    copied to S3 are skipped.

    Args:
        db (Session): Database session.
        check_only (bool): If True, report what would be removed without
            removing static files or database records.
        skip_project_ids (Optional[Set[UUID]]): Projects already covered by
            cleanup_projects in this run. Their flights are skipped so a
            check-only run does not count the same files twice.

    Returns:
        Dict[str, Any]: Result record described by common.new_stats.
    """
    stats = new_stats()
    skip_project_ids = skip_project_ids or set()
    deactivated_flights_query = select(Flight.id, Flight.project_id).where(
        and_(
            Flight.is_active.is_(False),
            Flight.deactivated_at < get_retention_cutoff(),
        )
    )
    with db as session:
        deactivated_flights = session.execute(deactivated_flights_query).all()
        flight_ids_with_s3_objects = get_flight_ids_with_s3_objects(session)

    for flight_id, project_id in deactivated_flights:
        if project_id in skip_project_ids:
            continue
        if flight_id in flight_ids_with_s3_objects:
            log_s3_skip("flight", flight_id)
            stats["items_skipped"] += 1
            continue
        try:
            static_dir = get_flight_dir(project_id, flight_id)
            dir_size = remove_static_dir(static_dir, check_only)
            if not check_only:
                crud.flight.remove(db, id=flight_id)
            log_removal("flight", flight_id, static_dir, dir_size, check_only)
            stats["items_removed"] += 1
            stats["space_freed_up"] += dir_size
            stats["removed_ids"].add(flight_id)
        except Exception:
            logger.exception("Failed to remove flight %s", flight_id)
            stats["failures"] += 1

    return stats
