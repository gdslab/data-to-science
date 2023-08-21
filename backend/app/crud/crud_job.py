from fastapi.encoders import jsonable_encoder
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


job = CRUDJob(Job)
