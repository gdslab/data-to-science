from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.job import JobCreate, State, Status


def create_job(
    db: Session,
    extra: Optional[dict] = None,
    name: str = "test-job",
    state: State = State.PENDING,
    status: Status = Status.WAITING,
    start_time: datetime = datetime.now(tz=timezone.utc),
    data_product_id: Optional[UUID] = None,
    raw_data_id: Optional[UUID] = None,
) -> models.Job:
    job_in = JobCreate(
        name=name,
        state=state,
        status=status,
        start_time=start_time,
        data_product_id=data_product_id,
        raw_data_id=raw_data_id,
    )
    if extra:
        job_in.extra = extra
    return crud.job.create_job(db, obj_in=job_in)
