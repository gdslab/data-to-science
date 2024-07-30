import logging
import os
import shutil
from typing import Dict

from sqlalchemy import and_, select, text
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.crud.crud_admin import get_static_directory_size
from app.models import Flight

logger = logging.getLogger("__name__")


def remove_flight_dir(project_id: str, flight_id: str, check_only: bool) -> int:
    # path to flight's static file directory
    if os.environ.get("RUNNING_TESTS") == "1":
        root_static_dir = settings.TEST_STATIC_DIR
    else:
        root_static_dir = settings.STATIC_DIR
    static_dir = os.path.join(
        root_static_dir, "projects", project_id, "flights", flight_id
    )
    # remove flight directory and all sub-directories
    if os.path.isdir(static_dir):
        dir_size = get_static_directory_size(static_dir)
        if not check_only:
            shutil.rmtree(static_dir)
        return dir_size
    else:
        return 0


def cleanup_flights(db: Session, check_only: bool = False) -> Dict:
    # track flights removed and space freed up
    stats = {"items_removed": 0, "space_freed_up": 0}
    #  query for flights deactivated more than two weeks ago
    two_weeks_ago = text("now() - interval '2 week'")
    deactivated_flights_query = select(Flight).where(
        and_(Flight.is_active.is_(False), Flight.deactivated_at < two_weeks_ago)
    )
    with db as session:
        # execute query
        deactivated_flights = session.scalars(deactivated_flights_query).unique().all()
        # remove flight directory from static files for each deactivated flight
        for deactivated_flight in deactivated_flights:
            dir_size = remove_flight_dir(
                str(deactivated_flight.project_id),
                str(deactivated_flight.id),
                check_only,
            )
            stats["items_removed"] += 1
            stats["space_freed_up"] += dir_size
            # delete database records for deactivated flight
            if not check_only:
                crud.flight.remove(db, id=deactivated_flight.id)

    return stats
