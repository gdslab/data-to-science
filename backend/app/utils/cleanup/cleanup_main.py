import argparse
import logging
import sys
from typing import Any, Dict, Set
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.utils.cleanup.cleanup_data_products_and_raw_data import (
    cleanup_data_products_and_raw_data,
)
from app.utils.cleanup.cleanup_flights import cleanup_flights
from app.utils.cleanup.cleanup_projects import cleanup_projects
from app.utils.cleanup.cleanup_stale_jobs import cleanup_stale_jobs
from app.utils.cleanup.common import RETENTION_WEEKS

logger = logging.getLogger(__name__)


def format_size(size_in_bytes: int) -> str:
    """Format a byte count for the report.

    Args:
        size_in_bytes (int): Size in bytes.

    Returns:
        str: Size in megabytes.
    """
    return f"{size_in_bytes / (1024 * 1024):.2f} MB"


def print_report(results: Dict[str, Dict[str, Any]], check_only: bool) -> None:
    """Print one line per category that ran, then the total space involved.

    Args:
        results (Dict[str, Dict[str, Any]]): Result record per category that ran.
        check_only (bool): If True, report what would have been removed.
    """
    action = "to be removed" if check_only else "removed"
    total_space = 0
    total_failures = 0
    for category, stats in results.items():
        total_space += stats["space_freed_up"]
        total_failures += stats["failures"]
        report_line = (
            f"{category} {action}: {stats['items_removed']} "
            f"({format_size(stats['space_freed_up'])})"
        )
        if stats["items_skipped"]:
            report_line += f", skipped: {stats['items_skipped']}"
        if stats["failures"]:
            report_line += f", failed: {stats['failures']}"
        print(report_line)

    space = "Space that will be freed up" if check_only else "Space freed up"
    print(f"{space}: {format_size(total_space)}")
    if total_failures:
        print(f"Failures: {total_failures}. See the log messages above for details.")


def run(db: Session, args: argparse.Namespace) -> Dict[str, Dict[str, Any]]:
    """Run each cleanup category that was not skipped and report the results.

    Records removed by an earlier category are passed to the categories that
    follow it, so a project and the flights and data it contains are only
    counted once.

    Args:
        db (Session): Database session.
        args (argparse.Namespace): Parsed command line arguments.

    Returns:
        Dict[str, Dict[str, Any]]: Result record per category that ran.
    """
    results: Dict[str, Dict[str, Any]] = {}
    removed_project_ids: Set[UUID] = set()
    removed_flight_ids: Set[UUID] = set()

    if not args.skip_projects:
        results["Projects"] = cleanup_projects(db, args.check_only)
        removed_project_ids = results["Projects"]["removed_ids"]

    if not args.skip_flights:
        results["Flights"] = cleanup_flights(
            db, args.check_only, skip_project_ids=removed_project_ids
        )
        removed_flight_ids = results["Flights"]["removed_ids"]

    if not args.skip_data_products_and_raw_data:
        results["Data products and raw data"] = cleanup_data_products_and_raw_data(
            db,
            args.check_only,
            skip_project_ids=removed_project_ids,
            skip_flight_ids=removed_flight_ids,
        )

    if not args.skip_stale_jobs:
        results["Stale jobs"] = cleanup_stale_jobs(db, args.check_only)

    print_report(results, args.check_only)

    return results


def get_parser() -> argparse.ArgumentParser:
    """Build the command line parser.

    Returns:
        argparse.ArgumentParser: Parser for the cleanup script.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Removes projects, flights, data products, and raw data that have "
            f"been deactivated for more than {RETENTION_WEEKS} weeks, and "
            "upload jobs that never finished, along with their static files."
        )
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help=(
            "Only report the count and size of the items that would be removed. "
            "Does not remove static files or database records."
        ),
    )
    parser.add_argument(
        "--skip-projects",
        action="store_true",
        help="Skip removing deactivated projects.",
    )
    parser.add_argument(
        "--skip-flights",
        action="store_true",
        help="Skip removing deactivated flights.",
    )
    parser.add_argument(
        "--skip-data-products-and-raw-data",
        action="store_true",
        help="Skip removing deactivated data products and raw data.",
    )
    parser.add_argument(
        "--skip-stale-jobs",
        action="store_true",
        help="Skip removing stale upload jobs.",
    )
    return parser


def main() -> int:
    """Run the cleanup script.

    Returns:
        int: Exit code. Non-zero if the run failed or any item could not be
            removed.
    """
    args = get_parser().parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    try:
        db = SessionLocal()
    except Exception:
        logger.exception("Failed to establish database session.")
        return 1

    try:
        results = run(db, args)
    except Exception:
        logger.exception("Failed to cleanup data.")
        return 1
    finally:
        db.close()

    failures = sum(stats["failures"] for stats in results.values())
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
