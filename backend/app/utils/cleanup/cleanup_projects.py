import logging
from typing import Any, Dict, Optional, Set
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import crud
from app.models import Project
from app.utils.cleanup.common import (
    get_project_dir,
    get_project_ids_with_s3_objects,
    get_retention_cutoff,
    log_removal,
    log_s3_skip,
    new_stats,
    remove_static_dir,
)

logger = logging.getLogger(__name__)


def cleanup_projects(
    db: Session,
    check_only: bool = False,
    s3_project_ids: Optional[Set[UUID]] = None,
) -> Dict[str, Any]:
    """Remove projects deactivated longer ago than the retention window.

    Removing a project removes its static directory and, through database
    cascades, its flights, data products, and raw data. Projects that still
    have data copied to S3 are skipped.

    Args:
        db (Session): Database session.
        check_only (bool): If True, report what would be removed without
            removing static files or database records.
        s3_project_ids (Optional[Set[UUID]]): Projects held back because they
            still have data in S3, from common.get_project_ids_with_s3_objects.
            Looked up here when the caller has not already done so.

    Returns:
        Dict[str, Any]: Result record described by common.new_stats.
    """
    stats = new_stats()
    deactivated_projects_query = select(Project.id).where(
        and_(
            Project.is_active.is_(False),
            Project.deactivated_at < get_retention_cutoff(),
        )
    )
    with db as session:
        project_ids = list(session.scalars(deactivated_projects_query).all())
        project_ids_with_s3_objects = (
            get_project_ids_with_s3_objects(session)
            if s3_project_ids is None
            else s3_project_ids
        )

    for project_id in project_ids:
        if project_id in project_ids_with_s3_objects:
            log_s3_skip("project", project_id)
            stats["items_skipped"] += 1
            continue
        try:
            # remove the static files before the database record, so a failure
            # leaves behind a record that can be cleaned up on the next run
            # rather than files that no record points to
            static_dir = get_project_dir(project_id)
            dir_size = remove_static_dir(static_dir, check_only)
            if not check_only:
                crud.project.remove(db, id=project_id)
            log_removal("project", project_id, static_dir, dir_size, check_only)
            stats["items_removed"] += 1
            stats["space_freed_up"] += dir_size
            stats["removed_ids"].add(project_id)
        except Exception:
            logger.exception("Failed to remove project %s", project_id)
            stats["failures"] += 1

    return stats
