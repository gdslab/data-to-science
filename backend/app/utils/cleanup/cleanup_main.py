import argparse
import logging

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.utils.cleanup.cleanup_data_products_and_raw_data import (
    cleanup_data_products_and_raw_data,
)
from app.utils.cleanup.cleanup_flights import cleanup_flights
from app.utils.cleanup.cleanup_stale_jobs import cleanup_stale_jobs
from app.utils.cleanup.cleanup_projects import cleanup_projects


logger = logging.getLogger("__name__")


def run(db: Session, args: argparse.Namespace) -> None:
    # get arguments
    check_only = args.check_only
    skip_projects = args.skip_projects
    skip_flights = args.skip_flights
    skip_data_products_and_raw_data = args.skip_data_products_and_raw_data
    skip_stale_jobs = args.skip_stale_jobs

    space_freed_up = 0

    if not skip_projects:
        projects_info = cleanup_projects(db, check_only)
        space_freed_up += projects_info["space_freed_up"]

    if not skip_flights:
        flights_info = cleanup_flights(db, check_only)
        space_freed_up += flights_info["space_freed_up"]

    if not skip_data_products_and_raw_data:
        data_info = cleanup_data_products_and_raw_data(db, check_only)
        space_freed_up += data_info["space_freed_up"]

    if not skip_stale_jobs:
        jobs_info = cleanup_stale_jobs(db, check_only)
        space_freed_up += jobs_info["space_freed_up"]

    space_freed_up = f"{'%.2f' % ((space_freed_up / (1024 * 1024)))} MB"

    if check_only:
        print(f"Projects to be removed: {projects_info['items_removed']}")
        print(f"Flights to be removed: {flights_info['items_removed']}")
        print(f"Data products or raw data to be removed: {data_info['items_removed']}")
        print(f"Jobs to be removed: {jobs_info['items_removed']}")
        print(f"Space that will be freed up: {space_freed_up}")
    else:
        print(f"Projects removed: {projects_info['items_removed']}")
        print(f"Flights removed: {flights_info['items_removed']}")
        print(f"Data products or raw data removed: {data_info['items_removed']}")
        print(f"Jobs removed: {jobs_info['items_removed']}")
        print(f"Space freed up: {space_freed_up}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Removes deactivated projects, flights, and data products and ",
            "raw data older than two weeks.",
        )
    )
    parser.add_argument(
        "--check-only",
        type=bool,
        help=(
            "Only returns count and size of items to be removed. Does not remove ",
            "static files or database records.",
        ),
        default=0,
        required=False,
    )
    parser.add_argument(
        "--skip-projects",
        type=bool,
        help="Skip removing deactivated projects.",
        default=0,
        required=False,
    )
    parser.add_argument(
        "--skip-flights",
        type=bool,
        help="Skip removing deactivated flights.",
        default=0,
        required=False,
    )
    parser.add_argument(
        "--skip-data-products-and-raw-data",
        type=bool,
        help="Skip removing deactivated data products and raw data.",
        default=0,
        required=False,
    )
    parser.add_argument(
        "--skip-stale-jobs",
        type=bool,
        help="Skip removing stale jobs.",
        default=0,
        required=False,
    )

    args = parser.parse_args()

    try:
        # get database session
        db = SessionLocal()
    except Exception:
        logger.exception("Failed to establish database session.")

    try:
        run(db, args)
    except Exception:
        logger.exception("Failed to cleanup data")
    finally:
        db.close()
