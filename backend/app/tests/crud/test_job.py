from datetime import datetime

from sqlalchemy.orm import Session

from app import crud
from app.schemas.job import JobUpdate
from app.tests.utils.job import create_job


def test_create_job(db: Session) -> None:
    """Verify new job is created in database."""
    extra = {"extra": "could be anything"}
    name = "test job"
    state = "PENDING"
    status = "WAITING"
    start_time = datetime.now()
    job = create_job(
        db, extra=extra, name=name, state=state, status=status, start_time=start_time
    )
    assert job
    assert job.extra and job.extra.get("extra") == "could be anything"
    assert job.name == name
    assert job.state == state
    assert job.status == status
    assert job.start_time == start_time


def test_update_job(db: Session) -> None:
    """Verify existing job is updated in database."""
    job = create_job(db)
    job_in_update = JobUpdate(
        state="STARTED", status="INPROGRESS", extra={"extra": "could be anything"}
    )
    job_update = crud.job.update(db, db_obj=job, obj_in=job_in_update)
    assert job.id == job_update.id
    assert job.name == job_update.name
    assert job_update.state == "STARTED"
    assert job_update.status == "INPROGRESS"
    assert job_update.extra and job_update.extra.get("extra") == "could be anything"
