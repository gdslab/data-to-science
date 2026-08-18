import argparse
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.data_product import DataProduct
from app.models.flight import Flight
from app.models.job import Job
from app.models.project import Project
from app.models.raw_data import RawData
from app.schemas.data_product import DataProductUpdate
from app.schemas.job import JobUpdate, State, Status
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.job import create_job
from app.tests.utils.raw_data import SampleRawData
from app.tests.utils.user import create_user
from app.utils.cleanup.cleanup_data_products_and_raw_data import (
    cleanup_data_products_and_raw_data,
)
from app.utils.cleanup.cleanup_flights import cleanup_flights
from app.utils.cleanup.cleanup_main import run
from app.utils.cleanup.cleanup_projects import cleanup_projects
from app.utils.cleanup.cleanup_stale_jobs import cleanup_stale_jobs


def get_project_dir(project_id: UUID) -> str:
    """Return path to a project's directory in the test static directory."""
    return os.path.join(settings.TEST_STATIC_DIR, "projects", str(project_id))


def get_flight_dir(project_id: UUID, flight_id: UUID) -> str:
    """Return path to a flight's directory in the test static directory."""
    return os.path.join(get_project_dir(project_id), "flights", str(flight_id))


def get_data_dir(
    project_id: UUID, flight_id: UUID, data_dir: str, data_id: UUID
) -> str:
    """Return path to a data product or raw data directory in the test static
    directory."""
    return os.path.join(get_flight_dir(project_id, flight_id), data_dir, str(data_id))


def backdate(db: Session, model, record_id: UUID, weeks: int = 3) -> None:
    """Move a record's deactivated_at date far enough back to be cleaned up."""
    with db as session:
        session.execute(
            update(model)
            .where(model.id == record_id)
            .values(
                deactivated_at=datetime.now(tz=timezone.utc) - timedelta(weeks=weeks)
            )
        )
        session.commit()


def backdate_job(db: Session, job_id: UUID, weeks: int = 3) -> None:
    """Move a job's start time far enough back to be considered stale."""
    with db as session:
        session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(start_time=datetime.now(tz=timezone.utc) - timedelta(weeks=weeks))
        )
        session.commit()


def get_args(
    check_only: bool = False,
    skip_projects: bool = False,
    skip_flights: bool = False,
    skip_data_products_and_raw_data: bool = False,
    skip_stale_jobs: bool = False,
) -> argparse.Namespace:
    """Build the arguments cleanup_main.run expects."""
    return argparse.Namespace(
        check_only=check_only,
        skip_projects=skip_projects,
        skip_flights=skip_flights,
        skip_data_products_and_raw_data=skip_data_products_and_raw_data,
        skip_stale_jobs=skip_stale_jobs,
    )


def total(results: Dict[str, Dict[str, Any]], key: str) -> int:
    """Add up one counter across every category a cleanup run reported."""
    return sum(stats[key] for stats in results.values())


def record_exists(db: Session, model, record_id: UUID) -> bool:
    """Check whether a record is still in the database."""
    with db as session:
        return session.scalar(select(model.id).where(model.id == record_id)) is not None


def test_deactivated_project_cleanup(db: Session) -> None:
    """Projects deactivated longer than the retention window are removed."""
    user = create_user(db)
    # two projects are removed in one run, so a failure to keep the session
    # usable after the first removal is caught
    deactivated = [SampleDataProduct(db, user=user) for _ in range(2)]
    retained = SampleDataProduct(db, user=user)
    for data_product in deactivated:
        crud.project.deactivate(db, project_id=data_product.project.id, user_id=user.id)
        backdate(db, Project, data_product.project.id)

    for data_product in deactivated:
        assert os.path.isdir(get_project_dir(data_product.project.id))

    stats = cleanup_projects(db)

    assert stats["items_removed"] == 2
    assert stats["failures"] == 0
    assert stats["space_freed_up"] > 0
    for data_product in deactivated:
        assert not os.path.isdir(get_project_dir(data_product.project.id))
        assert not record_exists(db, Project, data_product.project.id)
        # flights and data products are removed with the project
        assert not record_exists(db, Flight, data_product.flight.id)
        assert not record_exists(db, DataProduct, data_product.obj.id)
    assert os.path.isdir(get_project_dir(retained.project.id))
    assert record_exists(db, Project, retained.project.id)


def test_deactivated_flight_cleanup(db: Session) -> None:
    """Flights deactivated longer than the retention window are removed."""
    user = create_user(db)
    deactivated = [SampleDataProduct(db, user=user) for _ in range(2)]
    retained = SampleDataProduct(db, user=user)
    for data_product in deactivated:
        crud.flight.deactivate(db, flight_id=data_product.flight.id)
        backdate(db, Flight, data_product.flight.id)

    stats = cleanup_flights(db)

    assert stats["items_removed"] == 2
    assert stats["failures"] == 0
    for data_product in deactivated:
        flight_dir = get_flight_dir(data_product.project.id, data_product.flight.id)
        assert not os.path.isdir(flight_dir)
        assert not record_exists(db, Flight, data_product.flight.id)
        # data products are removed with the flight
        assert not record_exists(db, DataProduct, data_product.obj.id)
        # the project the flight belonged to is left alone
        assert record_exists(db, Project, data_product.project.id)
    assert record_exists(db, Flight, retained.flight.id)


def test_deactivated_data_product_and_raw_data_cleanup(db: Session) -> None:
    """Data products and raw data deactivated longer than the retention window
    are removed, along with their static directories."""
    user = create_user(db)
    data_products = [SampleDataProduct(db, user=user) for _ in range(2)]
    all_raw_data = [SampleRawData(db, user=user) for _ in range(2)]
    retained = SampleDataProduct(db, user=user)
    for data_product in data_products:
        crud.data_product.deactivate(db, data_product_id=data_product.obj.id)
        backdate(db, DataProduct, data_product.obj.id)
    for raw_data in all_raw_data:
        crud.raw_data.deactivate(db, raw_data_id=raw_data.obj.id)
        backdate(db, RawData, raw_data.obj.id)

    stats = cleanup_data_products_and_raw_data(db)

    assert stats["items_removed"] == 4
    assert stats["failures"] == 0
    for data_product in data_products:
        data_product_dir = get_data_dir(
            data_product.project.id,
            data_product.flight.id,
            "data_products",
            data_product.obj.id,
        )
        assert not os.path.isdir(data_product_dir)
        assert not record_exists(db, DataProduct, data_product.obj.id)
    for raw_data in all_raw_data:
        raw_data_dir = get_data_dir(
            raw_data.project.id, raw_data.flight.id, "raw_data", raw_data.obj.id
        )
        assert not os.path.isdir(raw_data_dir)
        assert not record_exists(db, RawData, raw_data.obj.id)
    assert record_exists(db, DataProduct, retained.obj.id)


def test_check_only_reports_without_removing(db: Session) -> None:
    """A check-only run reports what it would remove and removes nothing."""
    user = create_user(db)
    data_product = SampleDataProduct(db, user=user)
    crud.project.deactivate(db, project_id=data_product.project.id, user_id=user.id)
    backdate(db, Project, data_product.project.id)
    project_dir = get_project_dir(data_product.project.id)

    stats = cleanup_projects(db, check_only=True)

    assert stats["items_removed"] == 1
    assert stats["space_freed_up"] > 0
    assert stats["failures"] == 0
    # nothing was actually removed
    assert os.path.isdir(project_dir)
    assert record_exists(db, Project, data_product.project.id)


def test_check_only_and_removal_report_the_same_totals(db: Session) -> None:
    """A deactivated project's flights and data products are only counted once,
    so a check-only run reports the same totals as the run that removes them."""
    user = create_user(db)
    data_product = SampleDataProduct(db, user=user)
    # deactivating a project cascades to its flights and data products, so all
    # three cleanup categories can see the same files
    crud.project.deactivate(db, project_id=data_product.project.id, user_id=user.id)
    backdate(db, Project, data_product.project.id)
    backdate(db, Flight, data_product.flight.id)
    backdate(db, DataProduct, data_product.obj.id)

    check_only_results = run(db, get_args(check_only=True))
    assert os.path.isdir(get_project_dir(data_product.project.id))

    removal_results = run(db, get_args())
    assert not os.path.isdir(get_project_dir(data_product.project.id))
    assert not record_exists(db, Project, data_product.project.id)

    # the project is reported once, not once per category that can see it
    assert total(check_only_results, "items_removed") == 1
    assert total(check_only_results, "items_removed") == total(
        removal_results, "items_removed"
    )
    assert total(check_only_results, "space_freed_up") == total(
        removal_results, "space_freed_up"
    )
    assert total(removal_results, "failures") == 0


def test_run_skips_categories(db: Session) -> None:
    """Skip flags leave a category alone without breaking the report."""
    user = create_user(db)
    data_product = SampleDataProduct(db, user=user)
    crud.project.deactivate(db, project_id=data_product.project.id, user_id=user.id)
    backdate(db, Project, data_product.project.id)

    results = run(db, get_args(skip_projects=True))

    assert "Projects" not in results
    assert total(results, "failures") == 0
    # the project category was skipped, so the project is still here
    assert os.path.isdir(get_project_dir(data_product.project.id))
    assert record_exists(db, Project, data_product.project.id)


def test_records_published_to_s3_are_skipped(db: Session) -> None:
    """Records with a copy in S3 are left in place so the S3 objects are not
    orphaned when the row holding their URL is removed."""
    user = create_user(db)
    published = SampleDataProduct(db, user=user)
    crud.data_product.update_s3_url(
        db,
        data_product_id=published.obj.id,
        s3_url="https://bucket.s3.amazonaws.com/published.tif",
    )
    crud.project.deactivate(db, project_id=published.project.id, user_id=user.id)
    backdate(db, Project, published.project.id)
    backdate(db, Flight, published.flight.id)
    backdate(db, DataProduct, published.obj.id)

    project_stats = cleanup_projects(db)
    flight_stats = cleanup_flights(db)
    data_stats = cleanup_data_products_and_raw_data(db)

    assert project_stats["items_skipped"] == 1
    assert project_stats["items_removed"] == 0
    assert flight_stats["items_skipped"] == 1
    assert flight_stats["items_removed"] == 0
    assert data_stats["items_skipped"] == 1
    assert data_stats["items_removed"] == 0
    assert os.path.isdir(get_project_dir(published.project.id))
    assert record_exists(db, DataProduct, published.obj.id)


def test_stale_upload_job_cleanup(db: Session) -> None:
    """Upload jobs that never succeeded are removed with the partial data they
    left behind."""
    user = create_user(db)
    stale = [SampleDataProduct(db, user=user) for _ in range(2)]
    retained = SampleDataProduct(db, user=user)
    for index, data_product in enumerate(stale):
        # the upload never finished, so the data product never completed its
        # initial processing
        crud.data_product.update(
            db,
            db_obj=data_product.obj,
            obj_in=DataProductUpdate(is_initial_processing_completed=False),
        )
        # one job is still stuck, the other finished as failed
        state = State.STARTED if index == 0 else State.COMPLETED
        status = Status.INPROGRESS if index == 0 else Status.FAILED
        crud.job.update(
            db,
            db_obj=data_product.job,
            obj_in=JobUpdate(name="upload-data-product", state=state, status=status),
        )
        backdate_job(db, data_product.job.id)

    stats = cleanup_stale_jobs(db)

    assert stats["items_removed"] == 2
    assert stats["failures"] == 0
    assert stats["space_freed_up"] > 0
    for data_product in stale:
        data_product_dir = get_data_dir(
            data_product.project.id,
            data_product.flight.id,
            "data_products",
            data_product.obj.id,
        )
        assert not os.path.isdir(data_product_dir)
        assert not record_exists(db, DataProduct, data_product.obj.id)
        # the job is removed along with the data product it belongs to
        assert not record_exists(db, Job, data_product.job.id)
    assert record_exists(db, DataProduct, retained.obj.id)


def test_stale_job_cleanup_keeps_completed_data_product(db: Session) -> None:
    """A data product that finished processing is kept even when an upload job
    for it looks stale."""
    user = create_user(db)
    data_product = SampleDataProduct(db, user=user)
    crud.job.update(
        db,
        db_obj=data_product.job,
        obj_in=JobUpdate(
            name="upload-data-product", state=State.STARTED, status=Status.INPROGRESS
        ),
    )
    backdate_job(db, data_product.job.id)

    stats = cleanup_stale_jobs(db)

    assert stats["items_removed"] == 0
    assert stats["items_skipped"] == 1
    data_product_dir = get_data_dir(
        data_product.project.id,
        data_product.flight.id,
        "data_products",
        data_product.obj.id,
    )
    assert os.path.isdir(data_product_dir)
    assert record_exists(db, DataProduct, data_product.obj.id)


def test_stale_job_cleanup_keeps_data_product_with_successful_job(
    db: Session,
) -> None:
    """A data product with a successful job is kept even when an upload job for
    it looks stale."""
    user = create_user(db)
    data_product = SampleDataProduct(db, user=user)
    crud.data_product.update(
        db,
        db_obj=data_product.obj,
        obj_in=DataProductUpdate(is_initial_processing_completed=False),
    )
    crud.job.update(
        db,
        db_obj=data_product.job,
        obj_in=JobUpdate(
            name="upload-data-product", state=State.STARTED, status=Status.INPROGRESS
        ),
    )
    backdate_job(db, data_product.job.id)
    # something else finished using the data product
    create_job(
        db,
        name="exg",
        state=State.COMPLETED,
        status=Status.SUCCESS,
        data_product_id=data_product.obj.id,
    )

    stats = cleanup_stale_jobs(db)

    assert stats["items_removed"] == 0
    assert stats["items_skipped"] == 1
    assert record_exists(db, DataProduct, data_product.obj.id)


def test_successful_upload_job_is_not_stale(db: Session) -> None:
    """An upload job that finished successfully is left alone no matter how old
    it is."""
    user = create_user(db)
    data_product = SampleDataProduct(db, user=user)
    crud.job.update(
        db,
        db_obj=data_product.job,
        obj_in=JobUpdate(
            name="upload-data-product", state=State.COMPLETED, status=Status.SUCCESS
        ),
    )
    backdate_job(db, data_product.job.id)

    stats = cleanup_stale_jobs(db)

    assert stats["items_removed"] == 0
    assert stats["items_skipped"] == 0
    assert record_exists(db, Job, data_product.job.id)
    assert record_exists(db, DataProduct, data_product.obj.id)


def test_stale_job_without_upload_record_is_removed(db: Session) -> None:
    """A stale upload job that has no data product left is removed on its own."""
    job = create_job(
        db,
        name="upload-data-product",
        state=State.STARTED,
        status=Status.INPROGRESS,
    )
    backdate_job(db, job.id)

    stats = cleanup_stale_jobs(db)

    assert stats["items_removed"] == 1
    assert stats["failures"] == 0
    assert not record_exists(db, Job, job.id)


def test_data_product_with_two_stale_jobs_is_only_removed_once(db: Session) -> None:
    """A retried upload leaves more than one stale job on the same data
    product, and the data product is still only removed and counted once."""
    user = create_user(db)
    data_product = SampleDataProduct(db, user=user)
    crud.data_product.update(
        db,
        db_obj=data_product.obj,
        obj_in=DataProductUpdate(is_initial_processing_completed=False),
    )
    crud.job.update(
        db,
        db_obj=data_product.job,
        obj_in=JobUpdate(
            name="upload-data-product", state=State.COMPLETED, status=Status.FAILED
        ),
    )
    backdate_job(db, data_product.job.id)
    retry = create_job(
        db,
        name="upload-data-product",
        state=State.STARTED,
        status=Status.INPROGRESS,
        data_product_id=data_product.obj.id,
    )
    backdate_job(db, retry.id)

    stats = cleanup_stale_jobs(db)

    assert stats["items_removed"] == 1
    assert stats["failures"] == 0
    assert not record_exists(db, DataProduct, data_product.obj.id)
    assert not record_exists(db, Job, retry.id)
