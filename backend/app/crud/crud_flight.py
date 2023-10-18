from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session

from app.crud.base import CRUDBase
from app.models.flight import Flight
from app.models.project import Project
from app.models.user_style import UserStyle
from app.schemas.flight import FlightCreate, FlightUpdate

from app.crud.crud_data_product import set_url_attr, set_user_style_attr


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

    def get_flight_by_id(
        self, db: Session, project_id: UUID, flight_id: UUID
    ) -> Flight | None:
        statement = (
            select(Flight)
            .join(Project)
            .where(Flight.project_id == project_id)
            .where(Flight.id == flight_id)
            .where(Project.is_active)
        )
        with db as session:
            flight = session.execute(statement).unique().scalar_one_or_none()
            return flight

    def get_multi_by_project(
        self,
        db: Session,
        project_id: UUID,
        upload_dir: str,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Flight]:
        statement = (
            select(Flight)
            .join(Project)
            .options(joinedload(Flight.data_products))
            .where(Flight.project_id == project_id)
            .where(Project.is_active)
        )
        with db as session:
            flights_with_data = session.execute(statement).scalars().unique().all()
            for flight in flights_with_data:
                for data_product in flight.data_products:
                    set_url_attr(data_product, upload_dir)
                    # check for saved user style
                    user_style_query = (
                        select(UserStyle)
                        .where(UserStyle.data_product_id == data_product.id)
                        .where(UserStyle.user_id == user_id)
                    )
                    user_style = session.execute(user_style_query).scalar_one_or_none()
                    if user_style:
                        set_user_style_attr(data_product, user_style.settings)

        return flights_with_data


flight = CRUDFlight(Flight)
