from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import selectinload, Session

from app.crud.base import CRUDBase
from app.models.flight import Flight
from app.schemas.flight import FlightCreate, FlightUpdate

from app.crud.crud_data_product import set_url_attr


class CRUDFlight(CRUDBase[Flight, FlightCreate, FlightUpdate]):
    def create_with_project(
        self, db: Session, obj_in: FlightCreate, project_id: UUID
    ) -> Flight:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = Flight(**obj_in_data, project_id=project_id)
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        return db_obj

    def get_multi_by_project(
        self,
        db: Session,
        project_id: UUID,
        upload_dir: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Flight]:
        statement = (
            select(Flight)
            .options(selectinload(Flight.data_products))
            .where(Flight.project_id == project_id)
        )
        with db as session:
            flights_with_data = session.scalars(statement).unique().all()
            for flight in flights_with_data:
                for data_product in flight.data_products:
                    set_url_attr(data_product, upload_dir)
        return flights_with_data


flight = CRUDFlight(Flight)
