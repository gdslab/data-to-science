from typing import Sequence, TypedDict
from uuid import UUID

from fastapi import status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, update, and_
from sqlalchemy.orm import joinedload, Session

from app import crud
from app.crud.base import CRUDBase
from app.crud.crud_data_product import (
    set_public_attr,
    set_url_attr,
    set_user_style_attr,
)
from app.models.data_product import DataProduct
from app.models.flight import Flight
from app.models.job import Job
from app.models.project import Project
from app.models.user_style import UserStyle
from app.models.utils.user import utcnow
from app.schemas.flight import FlightCreate, FlightUpdate


class ReadFlight(TypedDict):
    response_code: int
    message: str
    result: Flight | None


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
    ) -> ReadFlight:
        statement = (
            select(Flight)
            .where(
                and_(
                    Flight.project_id == project_id,
                    Flight.id == flight_id,
                    Flight.is_active,
                )
            )
            .join(Flight.project.and_(Project.is_active))
            .options(joinedload(Flight.data_products.and_(DataProduct.is_active)))
        )
        with db as session:
            flight = session.scalar(statement)
            if not flight:
                return {
                    "response_code": status.HTTP_404_NOT_FOUND,
                    "message": "Flight not found",
                    "result": None,
                }
            return {
                "response_code": status.HTTP_200_OK,
                "message": "Flight fetched successfully",
                "result": flight,
            }

    def get_multi_by_project(
        self,
        db: Session,
        project_id: UUID,
        upload_dir: str,
        user_id: UUID,
        include_all: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Flight]:
        statement = (
            select(Flight)
            .where(and_(Flight.project_id == project_id, Flight.is_active))
            .join(Flight.project.and_(Project.is_active))
            .options(joinedload(Flight.data_products.and_(DataProduct.is_active)))
        )
        with db as session:
            flights_with_data = session.execute(statement).scalars().unique().all()
            for flight in flights_with_data:
                # remove data product if its job status is FAILED or its state is not COMPLETED
                if not include_all:
                    keep_data_products = []
                    for data_product in flight.data_products:
                        job_query = select(Job).where(
                            Job.data_product_id == data_product.id
                        )
                        job = session.execute(job_query).scalar_one_or_none()
                        if job and job.state == "COMPLETED" and job.status == "SUCCESS":
                            keep_data_products.append(data_product)
                    flight.data_products = keep_data_products

                available_data_products = []
                for data_product in flight.data_products:
                    if data_product.filepath != "null":
                        if (
                            data_product.data_type == "point_cloud"
                            or data_product.data_type != "point_cloud"
                            and data_product.stac_properties
                        ):
                            # do not include geotiffs without stac props
                            available_data_products.append(data_product)
                            set_public_attr(
                                data_product, data_product.file_permission.is_public
                            )
                            set_url_attr(data_product, upload_dir)
                            # check for saved user style
                            user_style_query = (
                                select(UserStyle)
                                .where(UserStyle.data_product_id == data_product.id)
                                .where(UserStyle.user_id == user_id)
                            )
                            user_style = session.execute(
                                user_style_query
                            ).scalar_one_or_none()
                            if user_style:
                                set_user_style_attr(data_product, user_style.settings)
                flight.data_products = available_data_products
            return flights_with_data

    def deactivate(self, db: Session, flight_id: UUID) -> Flight | None:
        update_flight_sql = (
            update(Flight)
            .where(Flight.id == flight_id)
            .values(is_active=False, deactivated_at=utcnow())
        )
        with db as session:
            session.execute(update_flight_sql)
            session.commit()

        get_flight_sql = (
            select(Flight)
            .options(joinedload(Flight.data_products))
            .where(Flight.id == flight_id)
        )
        with db as session:
            deactivated_flight = session.execute(get_flight_sql).scalar()

        if deactivated_flight and len(deactivated_flight.data_products) > 0:
            for data_product in deactivated_flight.data_products:
                with db as session:
                    crud.data_product.deactivate(db, data_product_id=data_product.id)

        return deactivated_flight


flight = CRUDFlight(Flight)
