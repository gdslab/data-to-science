from pathlib import Path
from typing import Any, Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.raw_data import RawData
from app.schemas.raw_data import RawDataCreate, RawDataUpdate
from app.models.utils.user import utcnow


class CRUDRawData(CRUDBase[RawData, RawDataCreate, RawDataUpdate]):
    def create_with_flight(
        self, db: Session, obj_in: RawDataCreate, flight_id: UUID
    ) -> RawData:
        obj_in_data = jsonable_encoder(obj_in)
        raw_data = self.model(**obj_in_data, flight_id=flight_id)
        with db as session:
            session.add(raw_data)
            session.commit()
            session.refresh(raw_data)
            return raw_data

    def get_single_by_id(
        self, db: Session, raw_data_id: UUID, upload_dir: str
    ) -> RawData | None:
        stmt = (
            select(RawData)
            .where(RawData.id == raw_data_id)
            .where(RawData.is_active)
            .where(RawData.filepath != "null")
        )
        with db as session:
            raw_data = session.scalar(stmt)
            if raw_data:
                set_url_attr(raw_data, upload_dir)
            return raw_data

    def get_multi_by_flight(
        self,
        db: Session,
        flight_id: UUID,
        upload_dir: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[RawData]:
        stmt = (
            select(RawData)
            .where(RawData.flight_id == flight_id)
            .where(RawData.is_active)
        )
        with db as session:
            all_raw_data = session.execute(stmt).scalars().all()
            all_raw_data_with_status = []
            for raw_data in all_raw_data:
                if raw_data.jobs and raw_data.jobs.status:
                    set_status_attr(raw_data, raw_data.jobs.status)
                else:
                    set_status_attr(raw_data, "SUCCESS")
                if raw_data.filepath != "null":
                    set_url_attr(raw_data, upload_dir)
                all_raw_data_with_status.append(raw_data)
        return all_raw_data_with_status

    def deactivate(self, db: Session, raw_data_id: UUID) -> RawData | None:
        update_raw_data_sql = (
            update(RawData)
            .where(RawData.id == raw_data_id)
            .values(is_active=False, deactivated_at=utcnow())
        )
        with db as session:
            session.execute(update_raw_data_sql)
            session.commit()

        return crud.raw_data.get(db, id=raw_data_id)


def set_status_attr(raw_data_obj: RawData, status: str | Any):
    setattr(raw_data_obj, "status", status)


def set_url_attr(raw_data_obj: RawData, upload_dir: str):
    static_url = settings.API_DOMAIN + settings.STATIC_DIR
    relative_path = Path(raw_data_obj.filepath).relative_to(upload_dir)
    setattr(raw_data_obj, "url", f"{static_url}/{str(relative_path)}")


raw_data = CRUDRawData(RawData)
