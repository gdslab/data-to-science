import shutil

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app import models
from app.core.config import settings
from app.schemas import SiteStatistics


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
        .select_from(models.User)
        .where(and_(models.User.is_approved, models.User.is_email_confirmed))
    )
    with db as session:
        user_count = session.scalar(user_count_query)

    # get total count of active projects
    project_count = 0
    project_count_query = (
        select(func.count("*"))
        .select_from(models.Project)
        .where(models.Project.is_active)
    )
    with db as session:
        project_count = session.scalar(project_count_query)

    # get total count of active flights
    flight_count = 0
    flight_count_query = (
        select(func.count("*"))
        .select_from(models.Flight)
        .where(models.Flight.is_active)
    )
    with db as session:
        flight_count = session.scalar(flight_count_query)

    # get total count of active data prodcuts
    data_product_count = 0
    data_product_count_query = (
        select(func.count("*"))
        .select_from(models.DataProduct)
        .where(models.DataProduct.is_active)
    )
    with db as session:
        data_product_count = session.scalar(data_product_count_query)

    # get total count of active raw data and add to data product count
    # raw_data_count = 0
    # raw_data_count_query = (
    #     select(func.count("*"))
    #     .select_from(models.RawData)
    #     .where(models.RawData.is_active)
    # )
    # with db as session:
    #     raw_data_count = session.scalar(raw_data_count_query)

    # data_product_count += raw_data_count

    # count of data products by data type
    # DATA_TYPES = ["dsm", "point_cloud", "ortho", "other"]
    dsm_count = 0
    ortho_count = 0
    point_cloud_count = 0
    other_count = 0

    # get total count of dsm data products
    dsm_count_query = (
        select(func.count("*"))
        .select_from(models.DataProduct)
        .where(
            and_(models.DataProduct.is_active, models.DataProduct.data_type == "dsm")
        )
    )
    with db as session:
        dsm_count = session.scalar(dsm_count_query)

    # get total count of ortho data products
    ortho_count_query = (
        select(func.count("*"))
        .select_from(models.DataProduct)
        .where(
            and_(
                models.DataProduct.is_active,
                models.DataProduct.data_type == "ortho",
            )
        )
    )
    with db as session:
        ortho_count = session.scalar(ortho_count_query)

    # get total count of point cloud data products
    point_cloud_count_query = (
        select(func.count("*"))
        .select_from(models.DataProduct)
        .where(
            and_(
                models.DataProduct.is_active,
                models.DataProduct.data_type == "point_cloud",
            )
        )
    )
    with db as session:
        point_cloud_count = session.scalar(point_cloud_count_query)

    # get total count of other data products
    other_count_query = (
        select(func.count("*"))
        .select_from(models.DataProduct)
        .where(
            and_(
                models.DataProduct.is_active,
                models.DataProduct.data_type != "dsm",
                models.DataProduct.data_type != "ortho",
                models.DataProduct.data_type != "point_cloud",
            )
        )
    )
    with db as session:
        other_count = session.scalar(other_count_query)

    data_products_dtype_count = {
        "dsm_count": dsm_count,
        "ortho_count": ortho_count,
        "point_cloud_count": point_cloud_count,
        "other_count": other_count,
    }

    total, used, free = shutil.disk_usage(settings.STATIC_DIR)
    storage_availability = {
        "total": bytes_to_gigabytes(total),
        "used": bytes_to_gigabytes(used),
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
