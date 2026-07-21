import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Literal, Optional, Sequence
from uuid import UUID

import rasterio
from fastapi.encoders import jsonable_encoder
from rasterio.errors import CRSError
from rasterio.warp import transform_bounds
from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import joinedload, Session

from app import crud
from app.api.utils import get_signature_for_data_product, get_static_dir
from app.core.config import settings
from app.crud.base import CRUDBase
from app.crud.crud_admin import get_static_directory_size
from app.db.session import SessionLocal
from app.models.constants import NON_RASTER_TYPES, PROCESSING_JOB_NAMES
from app.models.data_product import DataProduct
from app.models.data_product_like import DataProductLike
from app.models.data_product_metadata import DataProductMetadata
from app.models.data_product_view import DataProductView
from app.models.enums.project_type import ProjectType
from app.models.file_permission import FilePermission
from app.models.flight import Flight
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.job import Job
from app.models.user import User
from app.models.utils.utcnow import utcnow
from app.schemas.data_product import (
    DataProductCreate,
    DataProductUpdate,
)
from app.schemas.project_member import Role
from app.schemas.job import Status
from app.models.user_style import UserStyle

logger = logging.getLogger("__name__")


class CRUDDataProduct(CRUDBase[DataProduct, DataProductCreate, DataProductUpdate]):
    def create_with_flight(
        self, db: Session, obj_in: DataProductCreate, flight_id: UUID
    ) -> DataProduct:
        obj_in_data = jsonable_encoder(obj_in)
        data_product = DataProduct(**obj_in_data, flight_id=flight_id)

        # Calculate and cache raster metadata if this is a raster product
        if data_product.data_type not in NON_RASTER_TYPES:
            metadata = calculate_raster_metadata(data_product.filepath)
            if metadata:
                data_product.bbox = metadata["bbox"]
                data_product.crs = metadata["crs"]
                data_product.resolution = metadata["resolution"]

        with db as session:
            session.add(data_product)
            session.commit()
            session.refresh(data_product)
        crud.file_permission.create_with_data_product(db, file_id=data_product.id)
        return data_product

    def get_single_by_id(
        self, db: Session, data_product_id: UUID, user_id: UUID, upload_dir: str
    ) -> Optional[DataProduct]:
        liked_exists = (
            select(1)
            .where(
                and_(
                    DataProductLike.data_product_id == DataProduct.id,
                    DataProductLike.user_id == user_id,
                )
            )
            .exists()
            .label("liked")
        )
        like_count_sq = (
            select(func.count(DataProductLike.id))
            .where(DataProductLike.data_product_id == DataProduct.id)
            .scalar_subquery()
            .label("like_count")
        )
        view_count_sq = (
            select(func.count(DataProductView.id))
            .where(DataProductView.data_product_id == DataProduct.id)
            .scalar_subquery()
            .label("view_count")
        )
        data_product_query = select(DataProduct, liked_exists, like_count_sq, view_count_sq).where(
            and_(DataProduct.id == data_product_id, DataProduct.is_active)
        )
        user_style_query = select(UserStyle).where(
            and_(
                UserStyle.data_product_id == data_product_id,
                UserStyle.user_id == user_id,
            )
        )
        xml_metadata_query = select(DataProductMetadata).where(
            and_(
                DataProductMetadata.data_product_id == data_product_id,
                DataProductMetadata.category == "xml",
            )
        )
        with db as session:
            row = session.execute(data_product_query).one_or_none()
            user_style = session.execute(user_style_query).scalar_one_or_none()
            if row:
                data_product, liked, like_count, view_count = row
                set_like_attrs(data_product, like_count, liked)
                set_view_count_attr(data_product, view_count)
                set_spatial_metadata_attrs(data_product)
                set_signature_attr(data_product)
                set_url_attr(data_product, upload_dir)
                is_status_set = set_status_attr(data_product, data_product.jobs)
                if user_style:
                    set_user_style_attr(data_product, user_style.settings)
                xml_metadata = session.execute(xml_metadata_query).scalar_one_or_none()
                if xml_metadata:
                    set_xml_metadata_attr(data_product, xml_metadata)
                # do not return if record shows initial processing incomplete, and
                # there is not a job for the initial processing
                if is_status_set:
                    return data_product

        return None

    def get_public_data_product_by_id(
        self,
        db: Session,
        file_id: UUID,
        upload_dir: str,
        user_id: Optional[UUID] = None,
    ) -> Optional[DataProduct]:
        # Whether the requesting user has liked this data product. With user_id
        # None (anonymous/share read), `user_id == None` renders IS NULL and
        # matches no rows, so liked resolves to False.
        liked_exists = (
            select(1)
            .where(
                and_(
                    DataProductLike.data_product_id == DataProduct.id,
                    DataProductLike.user_id == user_id,
                )
            )
            .exists()
            .label("liked")
        )
        like_count_sq = (
            select(func.count(DataProductLike.id))
            .where(DataProductLike.data_product_id == DataProduct.id)
            .scalar_subquery()
            .label("like_count")
        )
        view_count_sq = (
            select(func.count(DataProductView.id))
            .where(DataProductView.data_product_id == DataProduct.id)
            .scalar_subquery()
            .label("view_count")
        )
        data_product_query = (
            select(DataProduct, liked_exists, like_count_sq, view_count_sq)
            .join(DataProduct.file_permission)
            .join(DataProduct.flight)
            .options(joinedload(DataProduct.file_permission))
            .options(joinedload(DataProduct.flight))
            .where(
                and_(
                    DataProduct.is_active,
                    DataProduct.id == file_id,
                    DataProduct.is_initial_processing_completed,
                )
            )
        )
        with db as session:
            # .unique() is required here because .options(joinedload(DataProduct.flight))
            # triggers Flight.data_products/raw_data (lazy="joined"), which duplicates the
            # parent DataProduct row; .unique() collapses those duplicates.
            row = session.execute(data_product_query).unique().one_or_none()
            if not row:
                return None
            data_product, liked, like_count, view_count = row
            set_like_attrs(data_product, like_count, liked)
            set_view_count_attr(data_product, view_count)
            if data_product.file_permission.is_public:
                set_spatial_metadata_attrs(data_product)
                set_signature_attr(data_product)
                set_url_attr(data_product, upload_dir)
                return data_product
            elif user_id:
                project_id = data_product.flight.project_id
                project_member = crud.project_member.get_by_project_and_member_id(
                    db, project_uuid=project_id, member_id=user_id
                )
                if project_member:
                    set_spatial_metadata_attrs(data_product)
                    set_signature_attr(data_product)
                    set_url_attr(data_product, upload_dir)
                    return data_product
                else:
                    return None
            else:
                return None

    def get_multi_by_flight(
        self, db: Session, flight_id: UUID, upload_dir: str, user_id: UUID
    ) -> Sequence[DataProduct]:
        liked_exists = (
            select(1)
            .where(
                and_(
                    DataProductLike.data_product_id == DataProduct.id,
                    DataProductLike.user_id == user_id,
                )
            )
            .exists()
            .label("liked")
        )
        like_count_sq = (
            select(func.count(DataProductLike.id))
            .where(DataProductLike.data_product_id == DataProduct.id)
            .scalar_subquery()
            .label("like_count")
        )
        view_count_sq = (
            select(func.count(DataProductView.id))
            .where(DataProductView.data_product_id == DataProduct.id)
            .scalar_subquery()
            .label("view_count")
        )
        data_products_query = (
            select(DataProduct, liked_exists, like_count_sq, view_count_sq)
            .join(DataProduct.file_permission)
            .join(DataProduct.jobs)
            .where(and_(DataProduct.flight_id == flight_id, DataProduct.is_active))
        )
        with db as session:
            rows = session.execute(data_products_query).unique().all()

            # Batch load all user styles to avoid N+1 queries
            data_product_ids = [row[0].id for row in rows]
            user_styles_by_data_product_id = {}
            if data_product_ids:
                user_styles_query = (
                    select(UserStyle)
                    .where(UserStyle.data_product_id.in_(data_product_ids))
                    .where(UserStyle.user_id == user_id)
                )
                user_styles = session.execute(user_styles_query).scalars().all()
                for user_style in user_styles:
                    user_styles_by_data_product_id[user_style.data_product_id] = (
                        user_style
                    )

            # Batch load all xml metadata to avoid N+1 queries
            xml_metadata_by_data_product_id = {}
            if data_product_ids:
                xml_metadata_query = select(DataProductMetadata).where(
                    and_(
                        DataProductMetadata.data_product_id.in_(data_product_ids),
                        DataProductMetadata.category == "xml",
                    )
                )
                xml_metadata_rows = session.execute(xml_metadata_query).scalars().all()
                for xml_metadata_row in xml_metadata_rows:
                    xml_metadata_by_data_product_id[
                        xml_metadata_row.data_product_id
                    ] = xml_metadata_row

            updated_data_products = []
            for row in rows:
                data_product, liked, like_count, view_count = row
                set_like_attrs(data_product, like_count, liked)
                set_view_count_attr(data_product, view_count)

                # if not a non-raster type, find user style settings for data product
                if data_product.data_type not in NON_RASTER_TYPES:
                    user_style = user_styles_by_data_product_id.get(data_product.id)
                    if user_style:
                        set_user_style_attr(data_product, user_style.settings)

                # Set additional attributes to be returned by API
                set_spatial_metadata_attrs(data_product)
                set_public_attr(data_product, data_product.file_permission.is_public)
                set_signature_attr(data_product)
                set_url_attr(data_product, upload_dir)
                is_status_set = set_status_attr(data_product, data_product.jobs)
                xml_metadata = xml_metadata_by_data_product_id.get(data_product.id)
                if xml_metadata:
                    set_xml_metadata_attr(data_product, xml_metadata)

                # Only include data product if a status was set
                if is_status_set and hasattr(data_product, "status"):
                    updated_data_products.append(data_product)

            return updated_data_products

    def update_bands(
        self, db: Session, data_product_id: UUID, updated_metadata: Dict
    ) -> Optional[DataProduct]:
        update_data_product_sql = (
            update(DataProduct)
            .values(stac_properties=updated_metadata)
            .where(DataProduct.id == data_product_id)
        )
        with db as session:
            session.execute(update_data_product_sql)
            session.commit()

        return crud.data_product.get(db, id=data_product_id)

    def update_data_type(
        self, db: Session, data_product_id: UUID, new_data_type: str
    ) -> Optional[DataProduct]:
        update_data_product_sql = (
            update(DataProduct)
            .values(data_type=new_data_type)
            .where(
                and_(
                    DataProduct.id == data_product_id,
                    ~func.lower(DataProduct.data_type).in_(
                        [dtype.lower() for dtype in NON_RASTER_TYPES]
                    ),
                    DataProduct.is_active == True,
                )
            )
        )
        with db as session:
            session.execute(update_data_product_sql)
            session.commit()

        return crud.data_product.get(db, id=data_product_id)

    def deactivate(self, db: Session, data_product_id: UUID) -> Optional[DataProduct]:
        update_data_product_sql = (
            update(DataProduct)
            .values(is_active=False, deactivated_at=utcnow())
            .where(DataProduct.id == data_product_id)
        )
        with db as session:
            session.execute(update_data_product_sql)
            session.commit()

        return crud.data_product.get(db, id=data_product_id)

    def set_file_size(self, db: Session, data_product_id: UUID) -> Optional[int]:
        """Compute and persist the on-disk byte size of a data product's directory.

        Captured at upload finalization (and by the backfill) so per-user data
        usage is a fast SQL SUM instead of a filesystem walk at read time.
        Returns the size in bytes, or None if the data product no longer exists.
        """
        with db as session:
            location = session.execute(
                select(Flight.project_id, DataProduct.flight_id)
                .join(Flight, Flight.id == DataProduct.flight_id)
                .where(DataProduct.id == data_product_id)
            ).first()
            if location is None:
                return None
            project_id, flight_id = location
            data_product_dir = os.path.join(
                get_static_dir(),
                "projects",
                str(project_id),
                "flights",
                str(flight_id),
                "data_products",
                str(data_product_id),
            )
            file_size = get_static_directory_size(data_product_dir)
            session.execute(
                update(DataProduct)
                .where(DataProduct.id == data_product_id)
                .values(file_size=file_size)
            )
            session.commit()
        return file_size

    def update_s3_url(self, db: Session, data_product_id: UUID, s3_url: str) -> None:
        """Set the s3_url for a single data product."""
        stmt = (
            update(DataProduct)
            .where(DataProduct.id == data_product_id)
            .values(s3_url=s3_url)
        )
        with db as session:
            session.execute(stmt)
            session.commit()

    def clear_s3_urls_for_project(self, db: Session, project_id: UUID) -> int:
        """Bulk clear s3_url for all data products in a project."""
        stmt = (
            update(DataProduct)
            .where(
                DataProduct.flight_id.in_(
                    select(Flight.id).where(Flight.project_id == project_id)
                ),
                DataProduct.s3_url.isnot(None),
            )
            .values(s3_url=None)
        )
        with db as session:
            result = session.execute(stmt)
            session.commit()
            return result.rowcount

    def get_data_products_with_s3_urls_for_project(
        self, db: Session, project_id: UUID
    ) -> Sequence[DataProduct]:
        """Return data products with non-null s3_url for a project."""
        stmt = select(DataProduct).where(
            DataProduct.flight_id.in_(
                select(Flight.id).where(Flight.project_id == project_id)
            ),
            DataProduct.s3_url.isnot(None),
            DataProduct.is_active,
        )
        with db as session:
            return session.execute(stmt).scalars().all()

    def _owned_project_ids_subquery(self, user_id: UUID):
        """Project IDs where user_id holds the OWNER role.

        Ownership is role-based, not the single Project.owner_id creator: the
        creator is added as a ProjectMember with role=OWNER, and other members
        can be promoted to OWNER. This captures all of them.
        """
        return select(ProjectMember.project_uuid).where(
            and_(
                ProjectMember.member_id == user_id,
                ProjectMember.role == Role.OWNER,
                ProjectMember.project_type == ProjectType.PROJECT,
            )
        )

    def _owned_data_product_ids_subquery(self, user_id: UUID):
        """Active data products belonging to projects owned by user_id."""
        return (
            select(DataProduct.id)
            .join(Flight, Flight.id == DataProduct.flight_id)
            .join(Project, Project.id == Flight.project_id)
            .where(
                and_(
                    Project.id.in_(self._owned_project_ids_subquery(user_id)),
                    Project.is_active,
                    Flight.is_active,
                    DataProduct.is_active,
                )
            )
        )

    def get_owner_stats(self, db: Session, user_id: UUID) -> Dict:
        """Aggregate view/like/visibility stats for data products owned by user_id."""
        owned_subq = self._owned_data_product_ids_subquery(user_id).subquery()
        owned_ids = select(owned_subq.c.id)
        with db as session:
            data_product_count = session.execute(
                select(func.count()).select_from(owned_subq)
            ).scalar_one()
            total_views = session.execute(
                select(func.count(DataProductView.id)).where(
                    DataProductView.data_product_id.in_(owned_ids)
                )
            ).scalar_one()
            total_likes = session.execute(
                select(func.count(DataProductLike.id)).where(
                    DataProductLike.data_product_id.in_(owned_ids)
                )
            ).scalar_one()
            public_count = session.execute(
                select(func.count(FilePermission.id)).where(
                    and_(
                        FilePermission.file_id.in_(owned_ids),
                        FilePermission.is_public,
                    )
                )
            ).scalar_one()
            project_count = session.execute(
                select(func.count(func.distinct(Project.id))).where(
                    and_(
                        Project.id.in_(self._owned_project_ids_subquery(user_id)),
                        Project.is_active,
                    )
                )
            ).scalar_one()
        return {
            "total_views": total_views,
            "total_likes": total_likes,
            "data_product_count": data_product_count,
            "public_count": public_count,
            "project_count": project_count,
        }

    def get_owner_views_trend(
        self, db: Session, user_id: UUID, weeks: int = 12
    ) -> List[Dict]:
        """Weekly view counts (oldest -> newest, zero-filled) for owned data products."""
        owned_subq = self._owned_data_product_ids_subquery(user_id).subquery()
        week_start_col = func.date_trunc("week", DataProductView.viewed_at).label(
            "week_start"
        )
        with db as session:
            rows = session.execute(
                select(week_start_col, func.count(DataProductView.id).label("views"))
                .where(
                    DataProductView.data_product_id.in_(select(owned_subq.c.id))
                )
                .group_by(week_start_col)
            ).all()

        views_by_week = {row.week_start.date(): row.views for row in rows}
        today = datetime.now(timezone.utc).date()
        current_week_start = today - timedelta(days=today.weekday())
        points = []
        for i in range(weeks - 1, -1, -1):
            week_start = current_week_start - timedelta(weeks=i)
            points.append(
                {
                    "week_start": week_start.isoformat(),
                    "views": views_by_week.get(week_start, 0),
                }
            )
        return points

    def get_owner_top(
        self,
        db: Session,
        user_id: UUID,
        metric: Literal["views", "likes"] = "views",
        limit: int = 5,
    ) -> List[Dict]:
        """Top owned data products ranked by view or like count."""
        view_count_sq = (
            select(func.count(DataProductView.id))
            .where(DataProductView.data_product_id == DataProduct.id)
            .scalar_subquery()
        )
        like_count_sq = (
            select(func.count(DataProductLike.id))
            .where(DataProductLike.data_product_id == DataProduct.id)
            .scalar_subquery()
        )
        order_col = view_count_sq if metric == "views" else like_count_sq
        query = (
            select(
                DataProduct.id,
                DataProduct.data_type,
                Project.id.label("project_id"),
                Project.title.label("project_name"),
                Flight.id.label("flight_id"),
                Flight.acquisition_date.label("flight_date"),
                view_count_sq.label("views"),
                like_count_sq.label("likes"),
            )
            .join(Flight, Flight.id == DataProduct.flight_id)
            .join(Project, Project.id == Flight.project_id)
            .where(
                and_(
                    Project.id.in_(self._owned_project_ids_subquery(user_id)),
                    Project.is_active,
                    Flight.is_active,
                    DataProduct.is_active,
                )
            )
            .order_by(order_col.desc(), DataProduct.id)
            .limit(limit)
        )
        with db as session:
            rows = session.execute(query).all()
        return [dict(row._mapping) for row in rows]

    def get_activity_counts(self, db: Session, user_id: UUID) -> Dict:
        """Distinct count of data products user_id has viewed / liked."""
        with db as session:
            viewed_count = session.execute(
                select(
                    func.count(func.distinct(DataProductView.data_product_id))
                ).where(DataProductView.user_id == user_id)
            ).scalar_one()
            liked_count = session.execute(
                select(
                    func.count(func.distinct(DataProductLike.data_product_id))
                ).where(DataProductLike.user_id == user_id)
            ).scalar_one()
        return {"viewed_count": viewed_count, "liked_count": liked_count}

    def get_recent_activity(
        self,
        db: Session,
        user_id: UUID,
        action: Literal["viewed", "liked"] = "viewed",
        limit: int = 3,
    ) -> List[Dict]:
        """Most recent data products user_id viewed or liked, with owner name."""
        if action == "viewed":
            activity_model = DataProductView
            timestamp_col = DataProductView.viewed_at
        else:
            activity_model = DataProductLike
            timestamp_col = DataProductLike.created_at

        last_action_sq = (
            select(func.max(timestamp_col))
            .where(
                and_(
                    activity_model.data_product_id == DataProduct.id,
                    activity_model.user_id == user_id,
                )
            )
            .scalar_subquery()
        )
        query = (
            select(
                DataProduct.id,
                DataProduct.data_type,
                Project.id.label("project_id"),
                Project.title.label("project_name"),
                Project.owner_id,
                Flight.id.label("flight_id"),
                Flight.acquisition_date.label("flight_date"),
                last_action_sq.label("last_action_at"),
            )
            .join(Flight, Flight.id == DataProduct.flight_id)
            .join(Project, Project.id == Flight.project_id)
            .where(
                and_(
                    DataProduct.id.in_(
                        select(activity_model.data_product_id).where(
                            activity_model.user_id == user_id
                        )
                    ),
                    DataProduct.is_active,
                )
            )
            .order_by(last_action_sq.desc())
            .limit(limit)
        )
        with db as session:
            rows = session.execute(query).all()
            owner_ids = {row.owner_id for row in rows}
            owners_by_id = {}
            if owner_ids:
                owners = session.execute(
                    select(User).where(User.id.in_(owner_ids))
                ).scalars().all()
                owners_by_id = {
                    owner.id: f"{owner.first_name} {owner.last_name}"
                    for owner in owners
                }

        return [
            {
                "id": row.id,
                "data_type": row.data_type,
                "project_id": row.project_id,
                "project_name": row.project_name,
                "owner_name": owners_by_id.get(row.owner_id, ""),
                "flight_id": row.flight_id,
                "flight_date": row.flight_date,
                "last_action_at": row.last_action_at,
            }
            for row in rows
        ]


def set_status_attr(data_product_obj: DataProduct, jobs: List[Job]) -> bool:
    """Sets current status of the upload process to the "status" attribute.

    Args:
        data_product_obj (RawData): Data product object.
        jobs (List[Job]): Jobs associated with data product object.

    Returns:
        bool: Return True if able to set a status, return False if not status set.
    """
    status: Optional[Status] = None
    if data_product_obj.is_initial_processing_completed:
        status = Status.SUCCESS
    else:
        for job in jobs:
            if job.name in PROCESSING_JOB_NAMES:
                status = job.status

    if status is None:
        # Data product record indicates initial processing is not completed, and
        # no upload job can be found for the data product record
        return False
    else:
        setattr(data_product_obj, "status", status)
        return True


def set_spatial_metadata_attrs(data_product: DataProduct) -> None:
    """Sets spatial metadata (bbox, crs, resolution) as attributes on the data product object.

    Uses cached database values when available. Falls back to calculating from
    the raster file for legacy records created before caching was implemented.

    Implements "lazy migration": When metadata is calculated via fallback, it is
    automatically persisted to the database so subsequent requests use the fast path.

    Args:
        data_product (DataProduct): Data product object.
    """
    # Skip if not a raster data product
    if data_product.data_type in NON_RASTER_TYPES:
        return

    # Use cached database values if available (fast path)
    if data_product.bbox:
        setattr(data_product, "bbox", tuple(data_product.bbox))

        if data_product.crs:
            setattr(data_product, "crs", data_product.crs)

        if data_product.resolution:
            setattr(data_product, "resolution", data_product.resolution)

        return

    # Fallback: calculate on-the-fly for legacy records without cached metadata
    # This implements lazy migration - calculates once, then persists to database
    # so subsequent requests use the fast cached path
    metadata = calculate_raster_metadata(data_product.filepath)
    if metadata:
        # Set as temporary attributes for this request
        setattr(data_product, "bbox", tuple(metadata["bbox"]))
        setattr(data_product, "crs", metadata["crs"])
        setattr(data_product, "resolution", metadata["resolution"])

        # Persist to database for future requests (lazy migration)
        # Use a separate session to avoid expiring objects in the main read session
        try:
            with SessionLocal() as migration_session:
                update_stmt = (
                    update(DataProduct)
                    .where(DataProduct.id == data_product.id)
                    .values(
                        bbox=metadata["bbox"],
                        crs=metadata["crs"],
                        resolution=metadata["resolution"],
                    )
                )
                migration_session.execute(update_stmt)
                migration_session.commit()
                logger.info(
                    f"Lazy migration: persisted spatial metadata for data product {data_product.id}"
                )
        except Exception as e:
            # Log error but don't fail the request - metadata is still set as attribute
            logger.warning(
                f"Failed to persist spatial metadata for data product {data_product.id}: {e}"
            )


def set_public_attr(data_product_obj: DataProduct, is_public: bool) -> None:
    setattr(data_product_obj, "public", is_public)


def set_signature_attr(data_product_obj: DataProduct) -> None:
    signature, expiration_timestamp = get_signature_for_data_product(
        data_product_obj.id
    )
    signature_prop = {"secure": signature, "expires": expiration_timestamp}
    setattr(data_product_obj, "signature", signature_prop)


def get_url(data_product_filepath: str, upload_dir: str) -> str:
    static_url = settings.API_DOMAIN + settings.STATIC_DIR
    relative_path = Path(data_product_filepath).relative_to(upload_dir)

    return f"{static_url}/{str(relative_path)}"


def set_url_attr(data_product_obj: DataProduct, upload_dir: str) -> None:
    try:
        url = get_url(data_product_obj.filepath, upload_dir)
        setattr(data_product_obj, "url", url)
    except ValueError:
        setattr(data_product_obj, "url", None)


def set_user_style_attr(data_product_obj: DataProduct, user_style: Dict) -> None:
    setattr(data_product_obj, "user_style", user_style)


def set_like_attrs(
    data_product_obj: DataProduct, like_count: int, liked: bool
) -> None:
    setattr(data_product_obj, "like_count", like_count)
    setattr(data_product_obj, "liked", liked)


def set_view_count_attr(data_product_obj: DataProduct, view_count: int) -> None:
    setattr(data_product_obj, "view_count", view_count)


def set_xml_metadata_attr(
    data_product_obj: DataProduct, xml_metadata: DataProductMetadata
) -> None:
    """Sets XML file metadata and contents to the "xml_metadata" attribute.

    Args:
        data_product_obj (DataProduct): Data product object.
        xml_metadata (DataProductMetadata): Metadata record with category "xml".
    """
    filepath = xml_metadata.properties.get("filepath")
    if not filepath:
        return
    try:
        with open(filepath, "r") as xml_file:
            content = xml_file.read()
    except OSError as e:
        logger.warning(
            f"Unable to read XML file for data product {data_product_obj.id}: {e}"
        )
        return
    setattr(
        data_product_obj,
        "xml_metadata",
        {
            "original_filename": xml_metadata.properties.get("original_filename", ""),
            "file_size": xml_metadata.properties.get("file_size", len(content)),
            "content": content,
        },
    )


def calculate_raster_metadata(filepath: str) -> Optional[Dict]:
    """Calculate bbox, CRS, and resolution from raster file.

    Args:
        filepath (str): Path to raster file.

    Returns:
        Optional[Dict]: Dictionary with bbox, crs, and resolution or None if not a raster.
            - bbox: list[float] - WGS84 bounding box [minx, miny, maxx, maxy]
            - crs: dict - {"epsg": int, "unit": str}
            - resolution: dict - {"x": float, "y": float, "unit": str}
    """
    if Path(filepath).suffix != ".tif":
        return None

    try:
        with rasterio.open(filepath) as src:
            # Get bounds in original CRS
            bounds = src.bounds

            # Transform to WGS84
            wgs84_bbox = transform_bounds(
                src.crs,
                "EPSG:4326",
                bounds.left,
                bounds.bottom,
                bounds.right,
                bounds.top,
            )

            # Get the linear unit from the CRS
            crs_unit = src.crs.linear_units if src.crs.linear_units else "unknown"

            return {
                "bbox": list(wgs84_bbox),  # [minx, miny, maxx, maxy]
                "crs": {"epsg": src.crs.to_epsg(), "unit": crs_unit},
                "resolution": {
                    "x": src.res[0],
                    "y": src.res[1],
                    "unit": crs_unit,  # Resolution uses the same unit as the CRS
                },
            }
    except (CRSError, Exception) as e:
        logger.exception(f"Failed to calculate raster metadata for {filepath}: {e}")
        return None


data_product = CRUDDataProduct(DataProduct)
