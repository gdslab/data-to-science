import argparse
import logging
import os
import shutil
from pathlib import Path
from typing import Union

from sqlalchemy import and_, or_, select, text
from sqlalchemy.orm import Session

from app import crud
from app.crud.crud_admin import get_static_directory_size
from app.db.session import SessionLocal
from app.models.data_product import DataProduct
from app.models.job import Job
from app.models.raw_data import RawData

logger = logging.getLogger("__name__")


def remove_static_data_dir(
    data: Union[DataProduct, RawData], data_dir: str, check_only: bool = False
) -> int:
    """Remove static directory for data product or raw data.

    Args:
        data (Union[DataProduct, RawData]): Data Product or Raw Data to be removed.
        data_dir (str): Folder containing data (e.g., "data_products" or "raw_data").

    Returns:
        int: Size of folder removed in bytes.
    """
    # construct path to data product or raw data
    project_id = str(data.flight.project_id)
    flight_id = str(data.flight.id)
    data_id = str(data.id)
    static_dir = os.path.join(
        "/static/projects", project_id, "flights", flight_id, data_dir, data_id
    )
    # remove data product or raw data from static files
    if os.path.isdir(static_dir):
        dir_size = get_static_directory_size(static_dir)
        if not check_only:
            shutil.rmtree(static_dir)
        return dir_size
    else:
        return 0


def run(db: Session, check_only: bool = False) -> None:
    # track items removed and space freed up
    stats = {"items_removed": 0, "space_freed_up": 0}
    # PART I
    # Clean up deactivated data products
    two_weeks_ago = text("now() - interval '2 week'")
    deactivated_data_products_query = select(DataProduct).where(
        and_(DataProduct.is_active == False, DataProduct.deactivated_at < two_weeks_ago)
    )
    with SessionLocal() as session:
        deactivated_data_products = session.scalars(
            deactivated_data_products_query
        ).all()
        # Remove data from file system before removing records from database
        for data_product in deactivated_data_products:
            dir_size = remove_static_data_dir(data_product, "data_products", check_only)
            stats["items_removed"] += 1
            stats["space_freed_up"] += dir_size
            # delete database records now that files have been removed
            if not check_only:
                crud.data_product.remove(db, id=data_product.id)

    # PART II
    # Clean up deactivated raw data
    two_weeks_ago = text("now() - interval '2 week'")
    deactivated_raw_data_query = select(RawData).where(
        and_(RawData.is_active == False, RawData.deactivated_at < two_weeks_ago)
    )
    with SessionLocal() as session:
        deactivated_raw_data = session.scalars(deactivated_raw_data_query).all()
        # Remove data from file system before removing records from database
        for raw_data in deactivated_raw_data:
            dir_size = remove_static_data_dir(raw_data, "raw_data", check_only)
            stats["items_removed"] += 1
            stats["space_freed_up"] += dir_size
            # delete database records now that files have been removed
            if not check_only:
                crud.raw_data.remove(db, id=raw_data.id)

    # PART III
    # Clean up raw data and data products from jobs that failed
    # Remove data from file system before removing records from database
    old_jobs_query = select(Job).where(
        and_(
            or_(Job.name == "upload-data-product", Job.name == "upload-raw-data"),
            Job.state != "COMPLETED",
            Job.status != "SUCCESS",
            Job.start_time < two_weeks_ago,
        )
    )
    with SessionLocal() as session:
        old_jobs = session.scalars(old_jobs_query).all()
        for job in old_jobs:
            if job.name == "upload-data-product":
                if job.data_product:
                    dir_size = remove_static_data_dir(
                        job.data_product, "data_products", check_only
                    )
                    stats["data_products_removed"] += 1
                    stats["space_freed_up"] += dir_size
                    # delete database records associated with the removed data product
                    if not check_only:
                        crud.data_product.remove(db, id=job.data_product.id)
                else:
                    # no data product to clean up, remove job
                    if not check_only:
                        crud.job.remove(db, id=job.id)
            elif job.name == "upload-raw-data":
                if job.raw_data:
                    dir_size = remove_static_data_dir(
                        job.raw_data, "raw_data", check_only
                    )
                    stats["data_products_removed"] += 1
                    stats["space_freed_up"] += dir_size
                    # delete database records associated with the removed raw data
                    if not check_only:
                        crud.raw_data.remove(db, id=job.raw_data.id)
                else:
                    # no raw data to clean up, remove job
                    if not check_only:
                        crud.job.remove(db, id=job.id)

    if check_only:
        print(f"Data products and raw data to be removed: {stats.get('items_removed')}")
        print(
            f"Space that will be freed up: {'%.2f' % ((stats.get('space_freed_up') / (1024 * 1024)))} MB"
        )
    else:
        print(f"Data products and raw data removed: {stats.get('items_removed')}")
        print(
            f"Space freed up: {'%.2f' % (stats.get('space_freed_up') / (1024 * 1024))} MB"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Removes deactivated data products and raw data older than two weeks."
    )
    parser.add_argument(
        "--check-only",
        type=bool,
        help="Only returns count and size of items to be removed. Does not remove static files or database records.",
        default=0,
        required=False,
    )

    args = parser.parse_args()

    try:
        # get database session
        db = SessionLocal()
        run(db, check_only=args.check_only)
    except Exception as e:
        logger.exception("Failed to cleanup data products")
    finally:
        db.close()
