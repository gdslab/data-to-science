from datetime import datetime, timezone, timedelta
from typing import List
from uuid import uuid4

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


def test_get_jobs_by_name_and_project_id(db: Session) -> None:
    """Verify getting jobs by name and project ID works correctly."""
    from uuid import uuid4

    project_id = uuid4()
    other_project_id = uuid4()

    # Create jobs with different names and project IDs
    job1 = create_job(
        db,
        name="stac_preview",
        extra={"project_id": str(project_id)},
        status=Status.INPROGRESS,
    )
    job2 = create_job(
        db,
        name="stac_preview",
        extra={"project_id": str(other_project_id)},
        status=Status.WAITING,
    )
    job3 = create_job(
        db,
        name="stac_publish",
        extra={"project_id": str(project_id)},
        status=Status.INPROGRESS,
    )
    job4 = create_job(
        db,
        name="stac_preview",
        extra={"project_id": str(project_id)},
        status=Status.SUCCESS,
    )

    # Test finding stac_preview jobs for project_id (should return 2: job1 and job4)
    jobs = crud.job.get_jobs_by_name_and_project_id(
        db, job_name="stac_preview", project_id=project_id
    )
    assert len(jobs) == 2
    job_ids = [job.id for job in jobs]
    assert job1.id in job_ids
    assert job4.id in job_ids

    # Test finding only processing jobs for project_id (should return 1: job1)
    processing_jobs = crud.job.get_jobs_by_name_and_project_id(
        db, job_name="stac_preview", project_id=project_id, processing=True
    )
    assert len(processing_jobs) == 1
    assert processing_jobs[0].id == job1.id

    # Test finding stac_publish jobs for project_id (should return 1: job3)
    publish_jobs = crud.job.get_jobs_by_name_and_project_id(
        db, job_name="stac_publish", project_id=project_id
    )
    assert len(publish_jobs) == 1
    assert publish_jobs[0].id == job3.id

    # Test finding stac_publish processing jobs for project_id (should return 1: job3)
    publish_processing_jobs = crud.job.get_jobs_by_name_and_project_id(
        db, job_name="stac_publish", project_id=project_id, processing=True
    )
    assert len(publish_processing_jobs) == 1
    assert publish_processing_jobs[0].id == job3.id

    # Test finding jobs for other_project_id (should return 1: job2)
    other_jobs = crud.job.get_jobs_by_name_and_project_id(
        db, job_name="stac_preview", project_id=other_project_id
    )
    assert len(other_jobs) == 1
    assert other_jobs[0].id == job2.id


def test_get_jobs_by_name_and_project_id_excludes_old_jobs(db: Session) -> None:
    """Verify that jobs older than the cutoff time are excluded when processing=True."""
    project_id = uuid4()

    # Create a recent job (should be included)
    recent_job = create_job(
        db,
        name="stac_preview",
        extra={"project_id": str(project_id)},
        status=Status.INPROGRESS,
        start_time=datetime.now(timezone.utc) - timedelta(hours=2),  # 2 hours ago
    )

    # Create an old job (should be excluded)
    old_job = create_job(
        db,
        name="stac_preview",
        extra={"project_id": str(project_id)},
        status=Status.INPROGRESS,
        start_time=datetime.now(timezone.utc) - timedelta(hours=25),  # 25 hours ago
    )

    # Set cutoff time to 24 hours ago
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

    # Test finding processing jobs with cutoff - should only return the recent job
    processing_jobs = crud.job.get_jobs_by_name_and_project_id(
        db,
        job_name="stac_preview",
        project_id=project_id,
        processing=True,
        cutoff_time=cutoff_time,
    )
    assert len(processing_jobs) == 1
    assert processing_jobs[0].id == recent_job.id

    # Test finding processing jobs without cutoff - should return both
    processing_jobs_no_cutoff = crud.job.get_jobs_by_name_and_project_id(
        db, job_name="stac_preview", project_id=project_id, processing=True
    )
    assert len(processing_jobs_no_cutoff) == 2
    job_ids = [job.id for job in processing_jobs_no_cutoff]
    assert recent_job.id in job_ids
    assert old_job.id in job_ids

    # Test finding all jobs (processing=False) - should return both regardless of cutoff
    all_jobs = crud.job.get_jobs_by_name_and_project_id(
        db, job_name="stac_preview", project_id=project_id, processing=False
    )
    assert len(all_jobs) == 2
    job_ids = [job.id for job in all_jobs]
    assert recent_job.id in job_ids
    assert old_job.id in job_ids
