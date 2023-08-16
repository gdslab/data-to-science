from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.flight import Flight
from app.schemas.flight import FlightCreate, FlightUpdate


class CRUDFlight(CRUDBase[Flight, FlightCreate, FlightUpdate]):
    def create_with_project(
        self,
        db: Session,
        *,
        obj_in: FlightCreate,
        project_id: UUID,
    ) -> Flight:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, project_id=project_id)
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        return db_obj


flight = CRUDFlight(Flight)
