"""Tests for admin CRUD operations."""
import pytest
from sqlalchemy.orm import Session

from app import crud
from app.crud.crud_admin import get_site_statistics
from app.schemas.file_permission import FilePermissionUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user


def test_get_site_statistics_basic(db: Session) -> None:
    """Test basic site statistics retrieval."""
    # Create test data
    user1 = create_user(db, is_approved=True, is_email_confirmed=True)
    user2 = create_user(db, is_approved=True, is_email_confirmed=True)

    project1 = create_project(db, owner_id=user1.id)
    project2 = create_project(db, owner_id=user2.id)

    flight1 = create_flight(db, project_id=project1.id)
    flight2 = create_flight(db, project_id=project2.id)

    data_product1 = SampleDataProduct(db, flight=flight1, user=user1, project=project1)
    data_product2 = SampleDataProduct(db, flight=flight2, user=user2, project=project2)

    # Get site statistics
    stats = get_site_statistics(db)

    # Verify counts (at least the ones we created)
    assert stats.user_count >= 2
    assert stats.project_count >= 2
    assert stats.flight_count >= 2
    assert stats.data_product_count >= 2
    assert stats.public_data_product_count >= 0  # None are public by default


def test_get_site_statistics_public_data_products(db: Session) -> None:
    """Test that public_data_product_count only counts active data products, not raw data."""
    # Create test data
    user = create_user(db, is_approved=True, is_email_confirmed=True)
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id)

    # Create 3 data products
    dp1 = SampleDataProduct(db, flight=flight, user=user, project=project)  # Will be made public and active
    dp2 = SampleDataProduct(db, flight=flight, user=user, project=project)  # Will be made public but deactivated
    dp3 = SampleDataProduct(db, flight=flight, user=user, project=project)  # Will remain private

    # Get initial count
    stats_before = get_site_statistics(db)
    initial_public_count = stats_before.public_data_product_count

    # Make dp1 public (should be counted)
    fp1 = crud.file_permission.get_by_data_product(db, file_id=dp1.obj.id)
    assert fp1 is not None
    crud.file_permission.update(
        db, db_obj=fp1, obj_in=FilePermissionUpdate(is_public=True)
    )

    # Make dp2 public then deactivate (should NOT be counted)
    fp2 = crud.file_permission.get_by_data_product(db, file_id=dp2.obj.id)
    assert fp2 is not None
    crud.file_permission.update(
        db, db_obj=fp2, obj_in=FilePermissionUpdate(is_public=True)
    )
    crud.data_product.deactivate(db, data_product_id=dp2.obj.id)

    # dp3 remains private (should NOT be counted)

    # Get updated statistics
    stats_after = get_site_statistics(db)

    # Should only count dp1 (public AND active)
    assert stats_after.public_data_product_count == initial_public_count + 1


def test_get_site_statistics_zero_counts(db: Session) -> None:
    """Test that site statistics handles zero counts correctly."""
    # This test assumes a fresh database or that we can clear all data
    # In a real test environment with fixtures, this might have baseline data
    stats = get_site_statistics(db)

    # All counts should be >= 0 (not None)
    assert stats.user_count >= 0
    assert stats.project_count >= 0
    assert stats.flight_count >= 0
    assert stats.data_product_count >= 0
    assert stats.public_data_product_count >= 0

    # Verify types
    assert isinstance(stats.user_count, int)
    assert isinstance(stats.project_count, int)
    assert isinstance(stats.flight_count, int)
    assert isinstance(stats.data_product_count, int)
    assert isinstance(stats.public_data_product_count, int)


def test_get_site_statistics_excludes_raw_data(db: Session) -> None:
    """Test that public_data_product_count does not include raw data."""
    from app.tests.utils.raw_data import SampleRawData

    # Create test data
    user = create_user(db, is_approved=True, is_email_confirmed=True)
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id)

    # Create a data product and make it public
    dp = SampleDataProduct(db, flight=flight, user=user, project=project)
    fp_dp = crud.file_permission.get_by_data_product(db, file_id=dp.obj.id)
    assert fp_dp is not None
    crud.file_permission.update(
        db, db_obj=fp_dp, obj_in=FilePermissionUpdate(is_public=True)
    )

    # Get count with just data product
    stats_before = get_site_statistics(db)
    count_with_dp = stats_before.public_data_product_count

    # Create raw data and make it public
    raw_data = SampleRawData(db, flight=flight, user=user, project=project)
    fp_raw = crud.file_permission.get_by_raw_data(db, raw_data_id=raw_data.obj.id)
    assert fp_raw is not None
    crud.file_permission.update(
        db, db_obj=fp_raw, obj_in=FilePermissionUpdate(is_public=True)
    )

    # Get count after adding public raw data
    stats_after = get_site_statistics(db)
    count_with_raw = stats_after.public_data_product_count

    # Count should NOT increase (raw data should not be counted)
    assert count_with_raw == count_with_dp
