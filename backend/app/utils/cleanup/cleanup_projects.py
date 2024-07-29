import logging
import os
import shutil
from typing import Dict

from sqlalchemy import and_, select, text
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.crud.crud_admin import get_static_directory_size
from app.models import Project

logger = logging.getLogger("__name__")


def remove_project_dir(project_id: str, check_only: bool) -> int:
    """Remove static directory for project.

    Args:
        project_id (str): ID of project that will be removed.
        check_only (bool): If true, data is removed. If false, data not removed.

    Returns:
        int: Size of directory to be removed.
    """
    # path to project's static file directory
    static_dir = os.path.join(settings.STATIC_DIR, "projects", project_id)
    # remove project directory and all sub-directories
    if os.path.isdir(static_dir):
        dir_size = get_static_directory_size(static_dir)
        if not check_only:
            shutil.rmtree(static_dir)
        return dir_size
    else:
        return 0


def cleanup_projects(db: Session, check_only: bool = False) -> Dict:
    # track projects removed and space freed up
    stats = {"items_removed": 0, "space_freed_up": 0}
    #  query for projects deactivated more than two weeks ago
    two_weeks_ago = text("now() - interval '2 week'")
    deactivated_projects_query = select(Project).where(
        and_(Project.is_active.is_(False), Project.deactivated_at < two_weeks_ago)
    )
    with db as session:
        # execute query
        deactivated_projects = session.scalars(deactivated_projects_query).all()
        # remove project directory from static files for each deactivated project
        for deactivated_project in deactivated_projects:
            dir_size = remove_project_dir(str(deactivated_project.id), check_only)
            stats["items_removed"] += 1
            stats["space_freed_up"] += dir_size
            # delete database records for deactivated project
            if not check_only:
                crud.project.remove(db, id=deactivated_project.id)

    return stats
