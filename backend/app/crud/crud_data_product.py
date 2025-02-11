import os
from pathlib import Path
from typing import Dict, List, Optional, Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import joinedload, Session

from app import crud
from app.api.utils import get_signature_for_data_product
from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.data_product import DataProduct
from app.models.job import Job
from app.models.utils.utcnow import utcnow
from app.schemas.data_product import (
    DataProductCreate,
    DataProductUpdate,
)
from app.schemas.job import Status
from app.models.user_style import UserStyle


class CRUDDataProduct(CRUDBase[DataProduct, DataProductCreate, DataProductUpdate]):
    def create_with_flight(
        self, db: Session, obj_in: DataProductCreate, flight_id: UUID
    ) -> DataProduct:
        obj_in_data = jsonable_encoder(obj_in)
        data_product = DataProduct(**obj_in_data, flight_id=flight_id)
        with db as session:
            session.add(data_product)
            session.commit()
            session.refresh(data_product)
        crud.file_permission.create_with_data_product(db, file_id=data_product.id)
        return data_product

    def get_single_by_id(
        self, db: Session, data_product_id: UUID, user_id: UUID, upload_dir: str
    ) -> Optional[DataProduct]:
        data_product_query = select(DataProduct).where(
            and_(DataProduct.id == data_product_id, DataProduct.is_active)
        )
        user_style_query = select(UserStyle).where(
            and_(
                UserStyle.data_product_id == data_product_id,
                UserStyle.user_id == user_id,
            )
        )
        with db as session:
            data_product = session.execute(data_product_query).scalar_one_or_none()
            user_style = session.execute(user_style_query).scalar_one_or_none()
            if data_product:
                set_url_attr(data_product, upload_dir)
                is_status_set = set_status_attr(data_product, data_product.jobs)
                if user_style:
                    set_user_style_attr(data_product, user_style.settings)
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
        data_product_query = (
            select(DataProduct)
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
            data_product = session.scalar(data_product_query)
            if data_product and data_product.file_permission.is_public:
                set_signature_attr(data_product)
                set_url_attr(data_product, upload_dir)
                return data_product
            elif data_product and user_id:
                project_id = data_product.flight.project_id
                project_member = crud.project_member.get_by_project_and_member_id(
                    db, project_id=project_id, member_id=user_id
                )
                if project_member:
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
        data_products_query = (
            select(DataProduct)
            .join(DataProduct.file_permission)
            .join(DataProduct.jobs)
            .where(and_(DataProduct.flight_id == flight_id, DataProduct.is_active))
        )
        with db as session:
            data_products = (
                session.execute(data_products_query).scalars().unique().all()
            )
            updated_data_products = []
            for data_product in data_products:
                # if not a point cloud, find user style settings for data product
                if data_product.data_type != "point_cloud":
                    user_style_query = select(UserStyle).where(
                        and_(
                            UserStyle.data_product_id == data_product.id,
                            UserStyle.user_id == user_id,
                        )
                    )
                    user_style = session.execute(user_style_query).scalar_one_or_none()
                    if user_style:
                        set_user_style_attr(data_product, user_style.settings)

                # Set additional attributes to be returned by API
                set_public_attr(data_product, data_product.file_permission.is_public)
                set_signature_attr(data_product)
                set_url_attr(data_product, upload_dir)
                is_status_set = set_status_attr(data_product, data_product.jobs)

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
                    func.lower(DataProduct.data_type) != "point_cloud",
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
        accepted_job_names = ["upload-data-product", "exg-process", "nvdi-process"]
        for job in jobs:
            if job.name in accepted_job_names:
                status = job.status

    if status is None:
        # Data product record indicates initial processing is not completed, and
        # no upload job can be found for the data product record
        return False
    else:
        setattr(data_product_obj, "status", status)
        return True


def set_public_attr(data_product_obj: DataProduct, is_public: bool) -> None:
    setattr(data_product_obj, "public", is_public)


def set_signature_attr(data_product_obj: DataProduct) -> None:
    signature, expiration_timestamp = get_signature_for_data_product(
        data_product_obj.id
    )
    signature_prop = {"secure": signature, "expires": expiration_timestamp}
    setattr(data_product_obj, "signature", signature_prop)


def set_url_attr(data_product_obj: DataProduct, upload_dir: str) -> None:
    try:
        static_url = settings.API_DOMAIN + settings.STATIC_DIR
        relative_path = Path(data_product_obj.filepath).relative_to(upload_dir)
        setattr(data_product_obj, "url", f"{static_url}/{str(relative_path)}")
    except ValueError:
        setattr(data_product_obj, "url", None)


def set_user_style_attr(data_product_obj: DataProduct, user_style: Dict) -> None:
    setattr(data_product_obj, "user_style", user_style)


data_product = CRUDDataProduct(DataProduct)
