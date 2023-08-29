from pathlib import Path
from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.raw_data import RawData
from app.schemas.raw_data import RawDataCreate, RawDataUpdate


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
        statement = select(RawData).where(RawData.id == raw_data_id)
        with db as session:
            raw_data = session.execute(statement).one_or_none()
            if raw_data:
                set_url_attr(raw_data[0], upload_dir)
                return raw_data[0]
            return None

    def get_multi_by_flight(
        self,
        db: Session,
        flight_id: UUID,
        upload_dir: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[RawData]:
        statement = select(RawData).where(RawData.flight_id == flight_id)
        with db as session:
            all_raw_data = session.execute(statement).all()
            all_raw_data_with_status = []
            for raw_data in all_raw_data:
                set_url_attr(raw_data[0], upload_dir)
                all_raw_data_with_status.append(raw_data[0])
        return all_raw_data_with_status


def set_url_attr(raw_data_obj: RawData, upload_dir: str):
    relative_path = Path(raw_data_obj.filepath).relative_to(upload_dir)
    setattr(raw_data_obj, "url", f"{settings.STATIC_URL}/{str(relative_path)}")


raw_data = CRUDRawData(RawData)
