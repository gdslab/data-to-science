from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.job import JobCreate


def create_job(
    db: Session,
    name: str = "test-job",
    state: str = "PENDING",
    status: str = "WAITING",
    start_time: datetime = datetime.now(),
    raw_data_id: UUID | None = None,
) -> models.Job:
    job_in = JobCreate(
        name=name,
        state=state,
        status=status,
        start_time=start_time,
        raw_data_id=raw_data_id,
    )
    return crud.job.create_job(db, obj_in=job_in)