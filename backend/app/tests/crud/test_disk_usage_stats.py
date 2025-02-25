import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.crud.crud_admin import get_disk_usage
from app.schemas.disk_usage_stats import DiskUsageStatsCreate, DiskUsageStatsUpdate
from app.tests.utils.data_product import SampleDataProduct


def test_create_disk_usage_stats(db: Session) -> None:
    """
    Test that a DiskUsageStats record is created with valid and logically consistent values.

    This test:
      - Adds a sample data product to ensure the static directory is valid.
      - Retrieves disk usage statistics for the test static directory.
      - Creates a new DiskUsageStats record using these statistics.
      - Asserts that the record has a valid ID and non-null fields.
      - Verifies that disk usage values are non-negative and do not exceed the total.

    Args:
        db (Session): Database session fixture.
    """
    # Add sample data product to static directory
    SampleDataProduct(db)

    # Get disk usage stats
    total, used, free = get_disk_usage(settings.TEST_STATIC_DIR)

    # Ensure total disk space is positive
    assert total > 0

    # Create disk usage stats record
    obj_in = DiskUsageStatsCreate(disk_free=free, disk_total=total, disk_used=used)
    disk_usage_stats = crud.disk_usage_stats.create(db, obj_in=obj_in)

    # Assert that the record is returned and has been assigned an ID
    assert disk_usage_stats is not None
    assert disk_usage_stats.id is not None

    # Check that disk usage fields are of the expected type and are non-negative
    assert isinstance(disk_usage_stats.disk_free, int)
    assert isinstance(disk_usage_stats.disk_total, int)
    assert isinstance(disk_usage_stats.disk_used, int)
    assert disk_usage_stats.disk_free >= 0
    assert disk_usage_stats.disk_total >= 0
    assert disk_usage_stats.disk_used >= 0

    # Verify that used and free values do not exceed the total disk space
    assert disk_usage_stats.disk_used <= disk_usage_stats.disk_total
    assert disk_usage_stats.disk_free <= disk_usage_stats.disk_total

    # Confirm that a timestamp is set when the record is created
    assert disk_usage_stats.recorded_at is not None


def test_read_disk_usage_stats(db: Session) -> None:
    """
    Test that a DiskUsageStats record can be read from the database.

    This test:
      - Adds a sample data product to ensure the static directory is valid.
      - Retrieves disk usage statistics for the test static directory.
      - Creates a new DiskUsageStats record using these statistics.
      - Reads the record from the database using its ID.
      - Asserts that the retrieved record matches the created record's values.

    Args:
        db (Session): Database session fixture.
    """
    # Add sample data product to static directory
    SampleDataProduct(db)

    # Get disk usage stats
    total, used, free = get_disk_usage(settings.TEST_STATIC_DIR)

    # Create disk usage stats record
    obj_in = DiskUsageStatsCreate(disk_free=free, disk_total=total, disk_used=used)
    created = crud.disk_usage_stats.create(db, obj_in=obj_in)

    # Read the record using its ID
    read_record = crud.disk_usage_stats.get(db, id=created.id)

    assert read_record is not None, "Expected to retrieve a record, got None"
    assert read_record.id == created.id, "Record IDs should match"
    assert read_record.disk_total == total, "Total disk space should match"
    assert read_record.disk_used == used, "Used disk space should match"
    assert read_record.disk_free == free, "Free disk space should match"


def test_read_latest_disk_usage_stats(db: Session) -> None:
    """
    Test that the latest DiskUsageStats record can be read from the database.

    This test:
      - Adds a sample data product to ensure the static directory is valid.
      - Retrieves disk usage statistics for the test static directory.
      - Creates multiple DiskUsageStats records with a delay between each creation.
      - Retrieves the latest record using the get_latest function.
      - Asserts that the latest record has the most recent timestamp compared to all others.

    Args:
        db (Session): Database session fixture.
    """
    # Add sample data product to static directory
    SampleDataProduct(db)

    # Get disk usage stats
    total, used, free = get_disk_usage(settings.TEST_STATIC_DIR)

    # Create disk usage stats creation object
    obj_in = DiskUsageStatsCreate(disk_free=free, disk_total=total, disk_used=used)

    # Create three new records with a 1 second delay between each
    for i in range(3):
        crud.disk_usage_stats.create(db, obj_in=obj_in)
        time.sleep(1)

    # Retrieve the latest record from the database
    most_recent_record = crud.disk_usage_stats.get_latest(db)

    # Retrieve all records from the database
    all_records = crud.disk_usage_stats.get_multi(db)

    assert most_recent_record is not None, "Expected a most recent record"
    assert all_records and len(all_records) == 3, "Expected three records to be created"

    # Verify that no record has a recorded_at timestamp more recent than the latest record
    for record in all_records:
        if record.id != most_recent_record.id:
            assert record.recorded_at < most_recent_record.recorded_at


def test_update_disk_usage_stats(db: Session) -> None:
    """
    Test that a DiskUsageStats record can be updated in the database.

    This test:
      - Adds a sample data product to ensure the static directory is valid.
      - Retrieves disk usage statistics for the test static directory.
      - Creates a new DiskUsageStats record using these statistics.
      - Updates one or more fields using the DiskUsageStatsUpdate schema.
      - Asserts that the updated record reflects the new values while unchanged fields remain intact.

    Args:
        db (Session): Database session fixture.
    """
    # Add sample data product to static directory
    SampleDataProduct(db)

    # Get disk usage stats
    total, used, free = get_disk_usage(settings.TEST_STATIC_DIR)

    # Create disk usage stats record
    obj_in = DiskUsageStatsCreate(disk_free=free, disk_total=total, disk_used=used)
    created = crud.disk_usage_stats.create(db, obj_in=obj_in)

    # Define update data with a new disk_used value
    new_used = used // 2
    update_data = DiskUsageStatsUpdate(
        disk_free=free,
        disk_total=total,
        disk_used=new_used,
        recorded_at=datetime.now(tz=timezone.utc),
    )

    # Update the disk usage stats record
    updated = crud.disk_usage_stats.update(db, db_obj=created, obj_in=update_data)

    assert updated is not None, "Expected an updated record"
    assert updated.id == created.id, "Record ID should remain unchanged"
    assert updated.disk_used == new_used, "disk_used should be updated"
    # Ensure that other fields remain unchanged
    assert updated.disk_total == total, "disk_total should remain unchanged"
    assert updated.disk_free == free, "disk_free should remain unchanged"


def test_delete_disk_usage_stats(db: Session) -> None:
    """
    Test that a DiskUsageStats record can be deleted from the database.

    This test:
      - Adds a sample data product to ensure the static directory is valid.
      - Retrieves disk usage statistics for the test static directory.
      - Creates a new DiskUsageStats record using these statistics.
      - Deletes the record using its ID.
      - Asserts that the deleted record is returned and cannot be retrieved afterward.

    Args:
        db (Session): Database session fixture.
    """
    # Add sample data product to static directory
    SampleDataProduct(db)

    # Get disk usage stats
    total, used, free = get_disk_usage(settings.TEST_STATIC_DIR)

    # Create disk usage stats record
    obj_in = DiskUsageStatsCreate(disk_free=free, disk_total=total, disk_used=used)
    created = crud.disk_usage_stats.create(db, obj_in=obj_in)

    # Delete the disk usage stats record
    deleted = crud.disk_usage_stats.remove(db, id=created.id)

    # Assert that the deleted record matches the created record
    assert deleted is not None, "Expected to receive the deleted record"
    assert (
        deleted.id == created.id
    ), "Deleted record should have the same ID as the created record"

    # Ensure that the record is no longer retrievable from the database
    assert (
        crud.disk_usage_stats.get(db, id=created.id) is None
    ), "Expected record to be None after deletion"
