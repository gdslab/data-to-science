from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app import crud
from app.schemas.job import JobUpdate, State, Status
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight
from app.tests.utils.job import create_job
from app.tests.utils.raw_data import SampleRawData


def test_create_job(db: Session) -> None:
    """Verify new job is created in database."""
    extra = {"extra": "could be anything"}
    name = "test job"
    state = State.PENDING
    status = Status.WAITING
    start_time = datetime.now(tz=timezone.utc)
    job = create_job(
        db, extra=extra, name=name, state=state, status=status, start_time=start_time
    )
    assert job
    assert job.extra and job.extra.get("extra") == "could be anything"
    assert job.name == name
    assert job.state == state
    assert job.status == status
    assert job.start_time.replace(tzinfo=timezone.utc) == start_time


def test_read_by_raw_data_id(db: Session) -> None:
    raw_data = SampleRawData(db)
    create_job(db, name="test-job", raw_data_id=raw_data.obj.id)
    jobs = crud.job.get_by_raw_data_id(
        db, job_name="test-job", raw_data_id=raw_data.obj.id
    )
    assert jobs
    assert isinstance(jobs, List)
    assert len(jobs) == 1
    assert jobs[0].name == "test-job"
    assert jobs[0].raw_data_id == raw_data.obj.id


def test_read_multi_by_flight_id(db: Session) -> None:
    flight = create_flight(db)
    data_product = SampleDataProduct(db, flight=flight, skip_job=True)
    raw_data = SampleRawData(db, flight=flight)
    create_job(db, name="test-job", data_product_id=data_product.obj.id)
    create_job(db, name="test-job", raw_data_id=raw_data.obj.id)
    jobs = crud.job.get_multi_by_flight(db, flight_id=flight.id)
    assert jobs
    assert isinstance(jobs, List)
    assert len(jobs) == 2


def test_update_job(db: Session) -> None:
    """Verify existing job is updated in database."""
    job = create_job(db)
    job_in_update = JobUpdate(
        state=State.STARTED,
        status=Status.INPROGRESS,
        extra={"extra": "could be anything"},
    )
    job_update = crud.job.update(db, db_obj=job, obj_in=job_in_update)
    assert job.id == job_update.id
    assert job.name == job_update.name
    assert job_update.state == State.STARTED
    assert job_update.status == Status.INPROGRESS
    assert job_update.extra and job_update.extra.get("extra") == "could be anything"
