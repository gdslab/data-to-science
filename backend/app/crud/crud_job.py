from typing import Optional, Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.data_product import DataProduct
from app.models.flight import Flight
from app.models.job import Job
from app.models.raw_data import RawData
from app.schemas.job import JobCreate, JobUpdate, State, Status


class CRUDJob(CRUDBase[Job, JobCreate, JobUpdate]):
    def create_job(self, db: Session, obj_in: JobCreate) -> Job:
        job_in = jsonable_encoder(obj_in)
        job = self.model(**job_in)
        with db as session:
            session.add(job)
            session.commit()
            session.refresh(job)
        return job

    def get_multi_by_flight(
        self, db: Session, flight_id: UUID, incomplete: bool = False
    ) -> Sequence[Job]:
        if incomplete:
            select_statement = (
                select(Job)
                .join(Job.data_product)
                .join(DataProduct.flight)
                .where(and_(Flight.id == flight_id, Job.state != State.COMPLETED))
                .union(
                    select(Job)
                    .join(Job.raw_data)
                    .join(RawData.flight)
                    .where(and_(Flight.id == flight_id, Job.state != State.COMPLETED))
                )
            )
        else:
            select_statement = (
                select(Job)
                .join(Job.data_product)
                .join(DataProduct.flight)
                .where(Flight.id == flight_id)
                .union(
                    select(Job)
                    .join(Job.raw_data)
                    .join(RawData.flight)
                    .where(Flight.id == flight_id)
                )
            )
        with db as session:
            jobs = session.scalars(select_statement).all()
            jobs2 = session.scalars(select(Job)).all()
            dp = session.scalars(select(DataProduct)).all()
            rd = session.scalars(select(RawData)).all()
            return jobs

    def get_by_raw_data_id(
        self,
        db: Session,
        job_name: str,
        raw_data_id: UUID,
        status: Optional[str] = None,
    ) -> Sequence[Job]:
        if status:
            select_statement = select(Job).where(
                and_(
                    Job.raw_data_id == raw_data_id,
                    Job.name == job_name,
                    Job.status == status,
                )
            )
        else:
            select_statement = select(Job).where(
                and_(Job.raw_data_id == raw_data_id, Job.name == job_name)
            )

        with db as session:
            jobs = session.scalars(select_statement).all()
            return jobs

    def get_raw_data_jobs_by_flight_id(
        self,
        db: Session,
        job_name: str,
        flight_id: UUID,
        processing: Optional[bool] = False,
    ) -> Sequence[Job]:
        """Returns raw data jobs that match job name, flight ID, and processing status.

        Args:
            db (Session): Database session.
            job_name (str): Name of job.
            flight_id (UUID): ID of flight associated with raw data.
            processing (Optional[bool], optional): True if only waiting/inprogress jobs should be returned. Defaults to False.

        Returns:
            List[Job]: Raw data jobs matching provided conditions.
        """
        if processing:
            select_statement = (
                select(Job)
                .join(Job.raw_data)
                .where(
                    and_(
                        Job.name == job_name,
                        or_(
                            Job.status == Status.WAITING,
                            Job.status == Status.INPROGRESS,
                        ),
                        RawData.flight_id == flight_id,
                    )
                )
            )
        else:
            select_statement = (
                select(Job)
                .join(Job.raw_data)
                .where(and_(Job.name == job_name, RawData.flight_id == flight_id))
            )

        with db as session:
            jobs = session.scalars(select_statement).all()
            return jobs


job = CRUDJob(Job)
