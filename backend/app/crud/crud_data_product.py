from pathlib import Path
from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.job import Job
from app.models.data_product import DataProduct
from app.schemas.data_product import DataProductCreate, DataProductUpdate


class CRUDDataProduct(CRUDBase[DataProduct, DataProductCreate, DataProductUpdate]):
    def create_with_flight(
        self, db: Session, obj_in: DataProductCreate, flight_id: UUID
    ) -> DataProduct:
        obj_in_data = jsonable_encoder(obj_in)
        data_product = self.model(**obj_in_data, flight_id=flight_id)
        with db as session:
            session.add(data_product)
            session.commit()
            session.refresh(data_product)
            return data_product

    def get_single_by_id(
        self, db: Session, data_product_id: UUID, upload_dir: str
    ) -> DataProduct | None:
        statement = (
            select(DataProduct, Job.status)
            .join(DataProduct.jobs)
            .where(DataProduct.id == data_product_id)
        )
        with db as session:
            data_product = session.execute(statement).one_or_none()
            if data_product:
                set_url_attr(data_product[0], upload_dir)
                set_status_attr(data_product[0], data_product[1])
                return data_product[0]
        return None

    def get_multi_by_flight(
        self,
        db: Session,
        flight_id: UUID,
        upload_dir: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[DataProduct]:
        statement = (
            select(DataProduct, Job.status)
            .join(DataProduct.jobs)
            .where(DataProduct.flight_id == flight_id)
        )
        with db as session:
            all_data_product = session.execute(statement).all()
            all_data_product_with_status = []
            for data_product in all_data_product:
                set_url_attr(data_product[0], upload_dir)
                if data_product[1]:
                    set_status_attr(data_product[0], data_product[1])
                else:
                    set_status_attr(data_product[0], "UNKNOWN")
                all_data_product_with_status.append(data_product[0])
        return all_data_product_with_status


def set_status_attr(data_product_obj: DataProduct, status: str):
    setattr(data_product_obj, "status", status)


def set_url_attr(data_product_obj: DataProduct, upload_dir: str):
    relative_path = Path(data_product_obj.filepath).relative_to(upload_dir)
    setattr(data_product_obj, "url", f"{settings.STATIC_URL}/{str(relative_path)}")


data_product = CRUDDataProduct(DataProduct)
