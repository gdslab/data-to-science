import logging
import os
import shutil
from typing import Optional, Tuple, Type, Union

from sqlalchemy import and_, ColumnElement, desc, func, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app import crud
from app.models import DataProduct, FilePermission, Flight, Project, User
from app.schemas import SiteStatistics


logger = logging.getLogger("__name__")


def get_static_directory_size(static_directory: str) -> int:
    """Walk down static directory and calculate total disk usage by static files.

    Args:
        static_directory (str): Path to static directory.

    Returns:
        int: Total disk usage in bytes.
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(static_directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size


def bytes_to_gigabytes(in_bytes: int) -> float:
    return round(in_bytes / (1024 * 1024 * 1024), 1)


def get_disk_usage(static_dir: str) -> Tuple[int, int, int]:
    """
    Compute disk usage statistics related to a static directory.

    This function retrieves overall disk capacity and free space for the filesystem
    containing `static_dir` using `shutil.disk_usage()`. It also calculates the disk
    space consumed solely by the files and subdirectories within `static_dir` (using
    `get_static_directory_size()`). The returned tuple is in the format:

        (total_space, used_in_static_dir, free_space)

    where:
      - total_space is the total capacity of the filesystem (in bytes),
      - used_in_static_dir is the disk space used by the contents of `static_dir` (in bytes), and
      - free_space is the available disk space on the filesystem (in bytes).

    Args:
        static_dir (str): The path to the static directory.

    Returns:
        Tuple[int, int, int]: A tuple containing the total disk space, the disk space used
        by the static directory, and the free disk space, all in bytes.
    """
    # Retrieve the disk statistics for the filesystem containing static_dir.
    total, _, free = shutil.disk_usage(static_dir)

    # Calculate disk usage for only the static directory.
    used_in_static_dir = get_static_directory_size(static_dir)

    return total, used_in_static_dir, free


def get_site_statistics(db: Session) -> SiteStatistics:
    """Generates site statistics for admin dashboard.

    Args:
        db (Session): Database session.

    Returns:
        SiteStatistics: Site statistics.
    """

    try:
        # Execute all counts in a single query for better performance
        counts_query = select(
            # Count of active users (approved and email confirmed)
            select(func.count("*"))
            .select_from(User)
            .where(and_(User.is_approved, User.is_email_confirmed))
            .scalar_subquery()
            .label("user_count"),
            # Count of active projects
            select(func.count("*"))
            .select_from(Project)
            .where(Project.is_active)
            .scalar_subquery()
            .label("project_count"),
            # Count of active flights
            select(func.count("*"))
            .select_from(Flight)
            .where(Flight.is_active)
            .scalar_subquery()
            .label("flight_count"),
            # Count of active data products
            select(func.count("*"))
            .select_from(DataProduct)
            .where(DataProduct.is_active)
            .scalar_subquery()
            .label("data_product_count"),
            # Count of public active data products (excludes raw data)
            select(func.count("*"))
            .select_from(FilePermission)
            .join(DataProduct, FilePermission.file_id == DataProduct.id)
            .where(and_(FilePermission.is_public, DataProduct.is_active))
            .scalar_subquery()
            .label("public_data_product_count"),
        )

        result = db.execute(counts_query).one()
        user_count = result.user_count
        project_count = result.project_count
        flight_count = result.flight_count
        data_product_count = result.data_product_count
        public_data_product_count = result.public_data_product_count

        # Verify all counts were successfully retrieved
        if any(
            count is None
            for count in [
                project_count,
                flight_count,
                data_product_count,
                user_count,
                public_data_product_count,
            ]
        ):
            raise ValueError("Failed to retrieve one or more site statistics counts")

        # Count of top three data product data types
        top_three_data_types_query = (
            select(
                DataProduct.data_type,
                func.count(DataProduct.data_type).label("count"),
            )
            .group_by(DataProduct.data_type)
            .where(DataProduct.is_active)
            .order_by(desc("count"))
            .limit(3)
        )
        top_three_data_types = db.execute(top_three_data_types_query).all()
    except Exception as e:
        # Log the error appropriately (ensure a logger is configured)
        logger.exception("Error retrieving site statistics")
        raise

    # Process the top three data types using an iterative approach
    top_counts = []
    top_three_total = 0
    for row in top_three_data_types:
        entry = {"name": row[0], "count": row[1]}
        top_counts.append(entry)
        top_three_total += row[1]

    data_product_dtype_count = {
        "first": top_counts[0] if len(top_counts) > 0 else None,
        "second": top_counts[1] if len(top_counts) > 1 else None,
        "third": top_counts[2] if len(top_counts) > 2 else None,
        "other": {"name": "other", "count": data_product_count - top_three_total},
    }

    # Pull latest disk usage stats from the database
    disk_usage = crud.disk_usage_stats.get_latest(db)

    if disk_usage:
        # Convert from bytes to gigabytes
        storage_availability = {
            "total": disk_usage.disk_total,
            "used": disk_usage.disk_used,
            "free": disk_usage.disk_free,
        }
    else:
        storage_availability = {"total": 0, "used": 0, "free": 0}

    return SiteStatistics(
        data_product_count=data_product_count,
        data_product_dtype_count=data_product_dtype_count,
        flight_count=flight_count,
        project_count=project_count,
        public_data_product_count=public_data_product_count,
        storage_availability=storage_availability,
        user_count=user_count,
    )
