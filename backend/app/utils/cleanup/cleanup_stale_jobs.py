import logging
import os
import shutil
from typing import Dict, Union

from sqlalchemy import and_, or_, select, text
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models import DataProduct, Job, RawData
from app.crud.crud_admin import get_static_directory_size
from app.schemas.job import State, Status


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
    if os.environ.get("RUNNING_TESTS") == "1":
        root_static_dir = settings.TEST_STATIC_DIR
    else:
        root_static_dir = settings.STATIC_DIR
    # construct path to data product or raw data
    project_id = str(data.flight.project_id)
    flight_id = str(data.flight.id)
    data_id = str(data.id)
    static_dir = os.path.join(
        root_static_dir, "projects", project_id, "flights", flight_id, data_dir, data_id
    )
    # remove data product or raw data from static files
    if os.path.isdir(static_dir):
        dir_size = get_static_directory_size(static_dir)
        if not check_only:
            shutil.rmtree(static_dir)
        return dir_size
    else:
        return 0


def cleanup_stale_jobs(db: Session, check_only: bool = False) -> Dict:
    # track jobs removed and space freed up
    stats = {"items_removed": 0, "space_freed_up": 0}
    # query for jobs that didn't finish and that are older than two weeks
    two_weeks_ago = text("now() AT TIME ZONE 'UTC' - interval '2 week'")
    stale_jobs_query = select(Job).where(
        and_(
            or_(Job.name == "upload-data-product", Job.name == "upload-raw-data"),
            Job.state != State.COMPLETED,
            Job.status != Status.SUCCESS,
            Job.start_time < two_weeks_ago,
        )
    )
    with db as session:
        # execute query
        stale_jobs = session.scalars(stale_jobs_query).all()
        # remove files associated with stale job
        for stale_job in stale_jobs:
            # check if data product
            if stale_job.name == "upload-data-product":
                if stale_job.data_product:
                    dir_size = remove_static_data_dir(
                        stale_job.data_product, "data_products", check_only
                    )
                    stats["items_removed"] += 1
                    stats["space_freed_up"] += dir_size
                    # delete data product associated with stale job from database
                    if not check_only:
                        crud.data_product.remove(db, id=stale_job.data_product.id)
                else:
                    # no data product to clean up, remove job
                    if not check_only:
                        crud.job.remove(db, id=stale_job.id)
            # check if raw data
            if stale_job.name == "upload-raw-data":
                if stale_job.raw_data:
                    dir_size = remove_static_data_dir(
                        stale_job.raw_data, "raw_data", check_only
                    )
                    stats["items_removed"] += 1
                    stats["space_freed_up"] += dir_size
                    # delete raw data associated with stale job from database
                    if not check_only:
                        crud.raw_data.remove(db, id=stale_job.raw_data.id)
                else:
                    # no raw data to clean up, remove job
                    if not check_only:
                        crud.job.remove(db, id=stale_job.id)

    return stats
