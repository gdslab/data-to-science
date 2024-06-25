import os
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select, update
from sqlalchemy.orm import joinedload, Session

from app import crud
from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.data_product import DataProduct
from app.models.file_permission import FilePermission
from app.schemas.data_product import DataProductCreate, DataProductUpdate
from app.models.user_style import UserStyle
from app.models.utils.user import utcnow


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
    ) -> DataProduct | None:
        data_product_query = (
            select(DataProduct)
            .where(DataProduct.id == data_product_id)
            .where(DataProduct.is_active)
        )
        user_style_query = (
            select(UserStyle)
            .where(UserStyle.data_product_id == data_product_id)
            .where(UserStyle.user_id == user_id)
        )
        with db as session:
            data_product = session.execute(data_product_query).scalar_one_or_none()
            user_style = session.execute(user_style_query).scalar_one_or_none()
            if data_product:
                set_url_attr(data_product, upload_dir)
                set_status_attr(data_product, data_product.jobs.status)
                if user_style:
                    set_user_style_attr(data_product, user_style.settings)
            return data_product

    def get_public_data_product_by_id(
        self, db: Session, file_id: UUID, upload_dir: str, user_id: UUID | None = None
    ) -> DataProduct | None:
        data_product_query = (
            select(DataProduct)
            .join(DataProduct.file_permission)
            .join(DataProduct.flight)
            .options(joinedload(DataProduct.file_permission))
            .options(joinedload(DataProduct.flight))
            .where(DataProduct.is_active)
            .where(DataProduct.id == file_id)
        )
        with db as session:
            data_product = session.scalar(data_product_query)
            if data_product and data_product.file_permission.is_public:
                set_url_attr(data_product, upload_dir)
                return data_product
            elif data_product and user_id:
                project_id = data_product.flight.project_id
                project_member = crud.project_member.get_by_project_and_member_id(
                    db, project_id=project_id, member_id=user_id
                )
                if project_member:
                    set_url_attr(data_product, upload_dir)
                    return data_product
                else:
                    return None
            else:
                return None

    def get_multi_by_flight(
        self,
        db: Session,
        flight_id: UUID,
        upload_dir: str,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[DataProduct]:
        data_products_query = (
            select(DataProduct)
            .join(DataProduct.file_permission)
            .where(DataProduct.flight_id == flight_id)
            .where(DataProduct.is_active)
        )
        with db as session:
            data_products = session.execute(data_products_query).scalars().all()
            updated_data_products = []
            for data_product in data_products:
                skip_data_product = False
                # if not a point cloud, find user style settings for data product
                if data_product.data_type != "point_cloud":
                    user_style_query = (
                        select(UserStyle)
                        .where(UserStyle.data_product_id == data_product.id)
                        .where(UserStyle.user_id == user_id)
                    )
                    user_style = session.execute(user_style_query).scalar_one_or_none()
                    if user_style:
                        set_user_style_attr(data_product, user_style.settings)
                set_public_attr(data_product, data_product.file_permission.is_public)
                set_url_attr(data_product, upload_dir)
                if data_product.jobs and data_product.jobs.status:
                    set_status_attr(data_product, data_product.jobs.status)
                else:
                    skip_data_product = True
                if not skip_data_product:
                    updated_data_products.append(data_product)

            return updated_data_products

    def deactivate(self, db: Session, data_product_id: UUID) -> DataProduct | None:
        update_data_product_sql = (
            update(DataProduct)
            .where(DataProduct.id == data_product_id)
            .values(is_active=False, deactivated_at=utcnow())
        )
        with db as session:
            session.execute(update_data_product_sql)
            session.commit()

        return crud.data_product.get(db, id=data_product_id)


def set_status_attr(data_product_obj: DataProduct, status: str | Any):
    setattr(data_product_obj, "status", status)


def set_public_attr(data_product_obj: DataProduct, is_public: bool):
    setattr(data_product_obj, "public", is_public)


def set_url_attr(data_product_obj: DataProduct, upload_dir: str):
    try:
        static_url = settings.API_DOMAIN + settings.STATIC_DIR
        relative_path = Path(data_product_obj.filepath).relative_to(upload_dir)
        setattr(data_product_obj, "url", f"{static_url}/{str(relative_path)}")
    except ValueError:
        setattr(data_product_obj, "url", None)


def set_user_style_attr(data_product_obj: DataProduct, user_style: dict):
    setattr(data_product_obj, "user_style", user_style)


data_product = CRUDDataProduct(DataProduct)
