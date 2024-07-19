from datetime import datetime

from sqlalchemy.orm import Session

from app import crud
from app.schemas.job import JobUpdate
from app.tests.utils.job import create_job
from app.tests.utils.raw_data import SampleRawData


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


def test_read_by_raw_data_id(db: Session) -> None:
    raw_data = SampleRawData(db)
    job = create_job(db, job_name="test-job", raw_data_id=raw_data.obj.id)
    assert job
    assert job.raw_data_id == raw_data.obj.id
    assert job.name == "test-job"


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
