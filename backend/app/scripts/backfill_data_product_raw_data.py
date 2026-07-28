"""Backfill data_products.raw_data_id for products created before provenance tracking.

Existing data products carry no link to the raw data upload they were derived
from. This script reconstructs that link heuristically: for each successful
``processing-raw-data`` job (which records its source ``raw_data_id``), it matches
data products in the same flight that were created just after the job finished.

Products are created in the same request that marks the processing job SUCCESS,
so the real gap between the job's ``end_time`` and each product's ``created_at`` is
milliseconds; ``--window`` only exists to absorb clock skew on old rows. A product
matched by more than one job is ambiguous and left untouched.

Runs as a dry run by default (prints proposed changes, writes nothing). Pass
``--apply`` to persist. The same pass also records the matched product ids in each
job's ``extra["data_products"]`` so the processing history can show its outputs.

Examples:
    python /app/app/scripts/backfill_data_product_raw_data.py
    python /app/app/scripts/backfill_data_product_raw_data.py --window 300
    python /app/app/scripts/backfill_data_product_raw_data.py --flight <uuid> --apply
"""

import argparse
import logging
import sys
from datetime import timedelta
from typing import Dict, List, NamedTuple, Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.data_product import DataProduct
from app.models.job import Job
from app.models.raw_data import RawData
from app.schemas.job import Status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data product types the external processing service produces from raw data.
TARGET_DATA_TYPES = ("point_cloud", "dem", "ortho")

PROCESSING_JOB_NAME = "processing-raw-data"


class Match(NamedTuple):
    product: DataProduct
    job: Job


def compute_matches(
    jobs: Sequence[Job],
    products: Sequence[DataProduct],
    window_seconds: int,
) -> tuple[List[Match], Dict[UUID, List[Job]]]:
    """Match products to the processing job that produced them.

    A product matches a job when it belongs to the job's flight and was created
    in the window ``[job.end_time, job.end_time + window_seconds]``. Products
    matched by exactly one job are returned as confident matches; products
    matched by more than one job are returned as ambiguous and left unlinked.

    Args:
        jobs: Successful processing-raw-data jobs, each with raw_data loaded.
        products: Candidate products (raw_data_id currently NULL).
        window_seconds: Seconds after a job's end_time a product may appear.

    Returns:
        Tuple of (confident matches, ambiguous product_id -> [jobs]).
    """
    window = timedelta(seconds=window_seconds)
    # product id -> jobs whose window contains it
    candidates: Dict[UUID, List[Job]] = {}
    products_by_id: Dict[UUID, DataProduct] = {p.id: p for p in products}

    for job in jobs:
        if job.end_time is None or job.raw_data is None:
            continue
        job_flight_id = job.raw_data.flight_id
        for product in products:
            if product.flight_id != job_flight_id:
                continue
            if product.created_at < job.end_time:
                continue
            if product.created_at > job.end_time + window:
                continue
            candidates.setdefault(product.id, []).append(job)

    matches: List[Match] = []
    ambiguous: Dict[UUID, List[Job]] = {}
    for product_id, matched_jobs in candidates.items():
        if len(matched_jobs) == 1:
            matches.append(Match(products_by_id[product_id], matched_jobs[0]))
        else:
            ambiguous[product_id] = matched_jobs

    return matches, ambiguous


def _load_jobs(db: Session, flight_id: Optional[UUID]) -> List[Job]:
    stmt = (
        select(Job)
        .join(RawData, Job.raw_data_id == RawData.id)
        .where(
            Job.name == PROCESSING_JOB_NAME,
            Job.status == Status.SUCCESS,
            Job.raw_data_id.is_not(None),
            Job.end_time.is_not(None),
        )
    )
    if flight_id is not None:
        stmt = stmt.where(RawData.flight_id == flight_id)
    return list(db.scalars(stmt).all())


def _load_candidate_products(
    db: Session, flight_id: Optional[UUID]
) -> List[DataProduct]:
    stmt = select(DataProduct).where(
        DataProduct.raw_data_id.is_(None),
        DataProduct.data_type.in_(TARGET_DATA_TYPES),
    )
    if flight_id is not None:
        stmt = stmt.where(DataProduct.flight_id == flight_id)
    return list(db.scalars(stmt).all())


def backfill(window_seconds: int, flight_id: Optional[UUID], apply: bool) -> None:
    with SessionLocal() as session:
        jobs = _load_jobs(session, flight_id)
        products = _load_candidate_products(session, flight_id)

        matches, ambiguous = compute_matches(jobs, products, window_seconds)

        for match in matches:
            product = match.product
            job = match.job
            delta = int((product.created_at - job.end_time).total_seconds())
            logger.info(
                "MATCH  job=%s raw_data=%s (%s) ended=%s -> product=%s type=%s "
                "created=+%ss",
                job.id,
                job.raw_data_id,
                job.raw_data.original_filename if job.raw_data else "?",
                job.end_time.isoformat(),
                product.id,
                product.data_type,
                delta,
            )

        for product_id, matched_jobs in ambiguous.items():
            product = next(p for p in products if p.id == product_id)
            logger.info(
                "SKIP-AMBIGUOUS product=%s type=%s jobs=%s",
                product_id,
                product.data_type,
                [str(j.id) for j in matched_jobs],
            )

        matched_count = len(matches)
        ambiguous_count = len(ambiguous)
        unmatched_count = len(products) - matched_count - ambiguous_count

        if apply and matches:
            # group product ids by job so we can also record outputs in extra
            products_by_job: Dict[UUID, List[Match]] = {}
            for match in matches:
                match.product.raw_data_id = match.job.raw_data_id
                products_by_job.setdefault(match.job.id, []).append(match)

            for job_id, job_matches in products_by_job.items():
                job = job_matches[0].job
                existing_extra = dict(job.extra) if job.extra else {}
                existing_extra["data_products"] = [
                    {"id": str(m.product.id), "data_type": m.product.data_type}
                    for m in job_matches
                ]
                job.extra = existing_extra

            session.commit()
            logger.info("Applied %d links.", matched_count)

        logger.info(
            "Summary: %d matched, %d ambiguous-skipped, %d products left unmatched.%s",
            matched_count,
            ambiguous_count,
            unmatched_count,
            "" if apply else " Re-run with --apply to write.",
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill data_products.raw_data_id from successful processing jobs"
        )
    )
    parser.add_argument(
        "--window",
        type=int,
        default=120,
        help=(
            "Seconds after a job's end_time a product may be created to count as "
            "its output (default: 120)"
        ),
    )
    parser.add_argument(
        "--flight",
        type=str,
        default=None,
        help="Limit backfill to a single flight id",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist the matches (default is a dry run that writes nothing)",
    )

    args = parser.parse_args()

    flight_id: Optional[UUID] = None
    if args.flight:
        try:
            flight_id = UUID(args.flight)
        except ValueError:
            logger.error("Invalid --flight id: %s", args.flight)
            sys.exit(1)

    backfill(window_seconds=args.window, flight_id=flight_id, apply=args.apply)


if __name__ == "__main__":
    main()
