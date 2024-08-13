import os
import shutil

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import DataProduct, Flight, Project, User
from app.schemas import SiteStatistics


def get_static_directory_size(static_directory: str) -> float:
    """Walk down static directory and calculate total disk usage by static files.

    Args:
        static_directory (str): Path to static directory.

    Returns:
        float: Total disk usage in bytes.
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(static_directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size


def bytes_to_gigabytes(in_bytes: float) -> float:
    return round(in_bytes / (1024 * 1024 * 1024), 1)


def get_site_statistics(db: Session) -> SiteStatistics:
    """Generates site statistics for admin dashboard.

    Args:
        db (Session): Database session.

    Returns:
        SiteStatistics: Site statistics.
    """
    # get total count of active users
    user_count = 0
    user_count_query = (
        select(func.count("*"))
        .select_from(User)
        .where(and_(User.is_approved, User.is_email_confirmed))
    )
    with db as session:
        user_count = session.scalar(user_count_query)

    # get total count of active projects
    project_count = 0
    project_count_query = (
        select(func.count("*")).select_from(Project).where(Project.is_active)
    )
    with db as session:
        project_count = session.scalar(project_count_query)

    # get total count of active flights
    flight_count = 0
    flight_count_query = (
        select(func.count("*")).select_from(Flight).where(Flight.is_active)
    )
    with db as session:
        flight_count = session.scalar(flight_count_query)

    # get total count of active data prodcuts
    data_product_count = 0
    data_product_count_query = (
        select(func.count("*")).select_from(DataProduct).where(DataProduct.is_active)
    )
    with db as session:
        data_product_count = session.scalar(data_product_count_query)

    # count of top five data product data types
    top_three_data_types_query = (
        select(DataProduct.data_type, func.count(DataProduct.data_type).label("count"))
        .group_by(DataProduct.data_type)
        .where(DataProduct.is_active)
        .order_by(desc("count"))
        .limit(3)
    )
    with db as session:
        top_three_data_types = session.execute(top_three_data_types_query).all()
        top_three_count = 0
        if len(top_three_data_types) > 0:
            first_count = {
                "name": top_three_data_types[0][0],
                "count": top_three_data_types[0][1],
            }
            top_three_count += top_three_data_types[0][1]
        else:
            first_count = None

        if len(top_three_data_types) > 1:
            second_count = {
                "name": top_three_data_types[1][0],
                "count": top_three_data_types[1][1],
            }
            top_three_count += top_three_data_types[1][1]
        else:
            second_count = None

        if len(top_three_data_types) > 2:
            third_count = {
                "name": top_three_data_types[2][0],
                "count": top_three_data_types[2][1],
            }
            top_three_count += top_three_data_types[2][1]
        else:
            third_count = None

        data_products_dtype_count = {
            "first": first_count,
            "second": second_count,
            "third": third_count,
            "other": {"name": "other", "count": data_product_count - top_three_count},
        }

    # "used" in this case is for the entire file sys, not just the provided directory
    total, used, free = shutil.disk_usage(settings.STATIC_DIR)
    storage_availability = {
        "total": bytes_to_gigabytes(total),
        "used": bytes_to_gigabytes(get_static_directory_size(settings.STATIC_DIR)),
        "free": bytes_to_gigabytes(free),
    }

    return SiteStatistics(
        data_product_count=data_product_count,
        data_product_dtype_count=data_products_dtype_count,
        flight_count=flight_count,
        project_count=project_count,
        storage_availability=storage_availability,
        user_count=user_count,
    )
