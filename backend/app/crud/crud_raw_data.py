from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

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

    def get_multi_by_flight(
        self, db: Session, flight_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[RawData]:
        statement = select(RawData).where(RawData.flight_id == flight_id)
        with db as session:
            raw_data = session.scalars(statement).all()
        return raw_data


raw_data = CRUDRawData(RawData)
