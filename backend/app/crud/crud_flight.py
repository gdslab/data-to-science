import os
from pathlib import Path
from typing import Sequence, TypedDict
from uuid import UUID

from fastapi import status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, or_, select, update
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
from app.models.vector_layer import VectorLayer
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
        has_raster: bool = False,
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
            # flights returned by crud
            final_flights = []
            for flight in flights_with_data:
                # remove data product if its upload job status is FAILED
                # or its state is not COMPLETED
                if not include_all:
                    keep_data_products = []
                    for data_product in flight.data_products:
                        job_query = select(Job).where(
                            and_(
                                Job.data_product_id == data_product.id,
                                or_(
                                    Job.name == "upload-data-product",
                                    Job.name == "exg-process",
                                    Job.name == "ndvi-process",
                                ),
                            )
                        )
                        job = session.execute(job_query).scalar_one_or_none()
                        if job and job.state == "COMPLETED" and job.status == "SUCCESS":
                            keep_data_products.append(data_product)
                    flight.data_products = keep_data_products

                available_data_products = []
                has_required_data_type = False
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
                            if has_raster and data_product.data_type != "point_cloud":
                                has_required_data_type = True
                flight.data_products = available_data_products

                if not has_raster or (has_raster and has_required_data_type):
                    final_flights.append(flight)

            return final_flights

    def change_flight_project(
        self, db: Session, flight_id: UUID, dst_project_id: UUID
    ) -> Flight:
        update_flight_statement = (
            update(Flight)
            .values(project_id=dst_project_id)
            .where(Flight.id == flight_id)
        )
        with db as session:
            session.execute(update_flight_statement)
            session.commit()

        # move any vector layer records associated with this flight
        update_vector_layers_statement = (
            update(VectorLayer)
            .values(project_id=dst_project_id)
            .where(VectorLayer.flight_id == flight_id)
        )
        with db as session:
            session.execute(update_vector_layers_statement)
            session.commit()

        with db as session:
            select_flight_statement = select(Flight).where(Flight.id == flight_id)
            updated_flight = session.scalar(select_flight_statement)

            # update filepath for any data products associated with flight
            if updated_flight and len(updated_flight.data_products) > 0:
                for data_product in updated_flight.data_products:
                    if data_product.filepath:
                        if os.environ.get("RUNNING_TESTS") == "1":
                            project_uuid_index = 4
                        else:
                            project_uuid_index = 3
                        # construct new filepath for data product
                        parts = list(Path(data_product.filepath).parts)
                        parts[project_uuid_index] = str(dst_project_id)
                        new_filepath = str(Path(*parts))
                        update_data_product_statement = (
                            update(DataProduct)
                            .values(filepath=new_filepath)
                            .where(DataProduct.id == data_product.id)
                        )
                        session.execute(update_data_product_statement)
                session.commit()
                session.refresh(updated_flight)

            return updated_flight

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
