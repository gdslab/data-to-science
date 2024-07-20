from typing import List, Optional
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate


class CRUDJob(CRUDBase[Job, JobCreate, JobUpdate]):
    def create_job(self, db: Session, obj_in: JobCreate):
        job_in = jsonable_encoder(obj_in)
        job = self.model(**job_in)
        with db as session:
            session.add(job)
            session.commit()
            session.refresh(job)
        return job

    def get_by_raw_data_id(
        self,
        db: Session,
        job_name: str,
        raw_data_id: UUID,
        status: Optional[str] = None,
    ) -> List[Job]:
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


job = CRUDJob(Job)
