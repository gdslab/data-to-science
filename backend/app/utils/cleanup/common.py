"""Shared helpers for the cleanup utilities.

Every cleanup module selects records that have aged past the retention window,
removes their static directory, removes their database records, and tracks how
much space it freed. The pieces they share live here so each module only has to
describe what it selects and what it removes.
"""

import logging
import os
import shutil
from typing import Any, Dict, Set
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import TextClause

from app.api.utils import get_static_dir
from app.crud.crud_admin import get_static_directory_size
from app.models import DataProduct, Flight, RawData

logger = logging.getLogger(__name__)

# Deactivated records and stale jobs are kept for this long before they are
# removed, so a deactivation can still be reversed by an administrator.
RETENTION_WEEKS = 2


def get_retention_cutoff() -> TextClause:
    """Return SQL expression for the oldest timestamp still inside the window.

    Records deactivated (or jobs started) before this timestamp are eligible for
    removal. The cutoff is calculated by the database so the result does not
    depend on the time zone of the machine running the cleanup.

    Returns:
        TextClause: SQL expression for the retention cutoff timestamp.
    """
    return text(f"now() - interval '{RETENTION_WEEKS} week'")


def new_stats() -> Dict[str, Any]:
    """Return an empty result record shared by every cleanup function.

    "removed_ids" holds the records the run removed. In check-only mode it holds
    the records that would have been removed, so a dry run and a real run
    report the same totals.

    Returns:
        Dict[str, Any]: Result record with zeroed counters.
    """
    return {
        "items_removed": 0,
        "space_freed_up": 0,
        "items_skipped": 0,
        "failures": 0,
        "removed_ids": set(),
    }


def get_project_dir(project_id: UUID) -> str:
    """Construct path to a project's static directory.

    Args:
        project_id (UUID): ID of project.

    Returns:
        str: Full path to the project directory.
    """
    return os.path.join(get_static_dir(), "projects", str(project_id))


def get_flight_dir(project_id: UUID, flight_id: UUID) -> str:
    """Construct path to a flight's static directory.

    Args:
        project_id (UUID): ID of project associated with the flight.
        flight_id (UUID): ID of flight.

    Returns:
        str: Full path to the flight directory.
    """
    return os.path.join(get_project_dir(project_id), "flights", str(flight_id))


def get_data_dir(
    project_id: UUID, flight_id: UUID, data_dir: str, data_id: UUID
) -> str:
    """Construct path to a data product's or raw data's static directory.

    Args:
        project_id (UUID): ID of project associated with the data.
        flight_id (UUID): ID of flight associated with the data.
        data_dir (str): Folder containing data (e.g., "data_products" or "raw_data").
        data_id (UUID): ID of the data product or raw data.

    Returns:
        str: Full path to the data product or raw data directory.
    """
    return os.path.join(get_flight_dir(project_id, flight_id), data_dir, str(data_id))


def remove_static_dir(static_dir: str, check_only: bool) -> int:
    """Remove a static directory and report how much space it used.

    Args:
        static_dir (str): Path to the directory to remove.
        check_only (bool): If True, the directory is measured but not removed.

    Returns:
        int: Size of the directory in bytes, or 0 if it does not exist.
    """
    if not os.path.isdir(static_dir):
        return 0
    dir_size = get_static_directory_size(static_dir)
    if not check_only:
        shutil.rmtree(static_dir)
    return dir_size


def log_removal(
    item_type: str, item_id: UUID, static_dir: str, dir_size: int, check_only: bool
) -> None:
    """Record a removal in the log so a run leaves an audit trail.

    Args:
        item_type (str): Type of record removed (e.g., "project").
        item_id (UUID): ID of the record removed.
        static_dir (str): Static directory removed with the record.
        dir_size (int): Size of the removed directory in bytes.
        check_only (bool): If True, nothing was actually removed.
    """
    logger.info(
        "%s %s %s (%s, %s bytes)",
        "Would remove" if check_only else "Removed",
        item_type,
        item_id,
        static_dir,
        dir_size,
    )


def get_project_ids_with_s3_objects(session: Session) -> Set[UUID]:
    """Find projects that still have data products or raw data copied to S3.

    A non-null s3_url means the record is published in a STAC catalog, or that
    an unpublish failed part way through and left objects behind. Either way the
    database row is the only record of the S3 object, so removing it would
    orphan that object. Callers skip these projects.

    Args:
        session (Session): Database session.

    Returns:
        Set[UUID]: IDs of projects with data still in S3.
    """
    data_product_projects = (
        select(Flight.project_id)
        .join(DataProduct, DataProduct.flight_id == Flight.id)
        .where(DataProduct.s3_url.isnot(None))
    )
    raw_data_projects = (
        select(Flight.project_id)
        .join(RawData, RawData.flight_id == Flight.id)
        .where(RawData.s3_url.isnot(None))
    )
    return set(session.scalars(data_product_projects).all()) | set(
        session.scalars(raw_data_projects).all()
    )


def get_flight_ids_with_s3_objects(session: Session) -> Set[UUID]:
    """Find flights that still have data products or raw data copied to S3.

    See get_project_ids_with_s3_objects for why these are skipped.

    Args:
        session (Session): Database session.

    Returns:
        Set[UUID]: IDs of flights with data still in S3.
    """
    data_product_flights = select(DataProduct.flight_id).where(
        DataProduct.s3_url.isnot(None)
    )
    raw_data_flights = select(RawData.flight_id).where(RawData.s3_url.isnot(None))
    return set(session.scalars(data_product_flights).all()) | set(
        session.scalars(raw_data_flights).all()
    )


def log_s3_skip(item_type: str, item_id: UUID) -> None:
    """Record that a record was left in place because it still has S3 objects.

    Args:
        item_type (str): Type of record skipped (e.g., "project").
        item_id (UUID): ID of the record skipped.
    """
    logger.warning(
        "Skipping %s %s: it still has data copied to S3. Unpublish the project "
        "from its STAC catalog so the S3 objects are removed first.",
        item_type,
        item_id,
    )
