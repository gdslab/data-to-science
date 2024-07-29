import logging
import os
import shutil
from typing import Dict, Union

from sqlalchemy import and_, select, text
from sqlalchemy.orm import Session

from app import crud
from app.models import DataProduct, RawData
from app.crud.crud_admin import get_static_directory_size


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


def cleanup_data_products_and_raw_data(db: Session, check_only: bool = False) -> Dict:
    # track data products and raw data items removed and space freed up
    stats = {"items_removed": 0, "space_freed_up": 0}
    # queries for deactivated data products and deactivated raw data
    two_weeks_ago = text("now() - interval '2 week'")
    deactivated_data_products_query = select(DataProduct).where(
        and_(
            DataProduct.is_active.is_(False), DataProduct.deactivated_at < two_weeks_ago
        )
    )
    deactivated_raw_data_query = select(RawData).where(
        and_(RawData.is_active.is_(False), RawData.deactivated_at < two_weeks_ago)
    )
    # remove deactivated data products
    with db as session:
        # execute query
        deactivated_data_products = session.scalars(
            deactivated_data_products_query
        ).all()
        # remove data product directory from static files for each data product
        for deactivated_data_product in deactivated_data_products:
            dir_size = remove_static_data_dir(
                deactivated_data_product, "data_products", check_only
            )
            stats["items_removed"] += 1
            stats["space_freed_up"] += dir_size
            # delete database records for deactivated data product
            if not check_only:
                crud.data_product.remove(db, id=deactivated_data_product.id)
    # remove deactivated raw data
    with db as session:
        # execute query
        deactivated_raw_data = session.scalars(deactivated_raw_data_query).all()
        # remove raw data directory from static files for each raw data
        for deactivated_raw in deactivated_raw_data:
            dir_size = remove_static_data_dir(deactivated_raw, "raw_data", check_only)
            stats["items_removed"] += 1
            stats["space_freed_up"] += dir_size
            # delete database records for deactivated raw data
            if not check_only:
                crud.raw_data.remove(db, id=deactivated_raw.id)

    return stats
