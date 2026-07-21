from datetime import date

from sqlalchemy.orm import Session

from app import crud
from app.schemas.data_product import DataProductUpdate
from app.schemas.raw_data import RawDataUpdate
from app.schemas.role import Role
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_like import create_data_product_like
from app.tests.utils.data_product_view import create_data_product_view
from app.tests.utils.flight import create_flight
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.raw_data import SampleRawData
from app.tests.utils.user import create_user


def test_get_activity_summary_active_counts_and_monotonic_funnel(db: Session) -> None:
    # One user marked active (sets last_activity_at), one left inactive.
    active_user = create_user(db)
    crud.user.update_last_login(db, user=active_user)
    create_user(db)  # inactive but approved + confirmed
    # A project created by the active user advances the final funnel stage.
    SampleDataProduct(db, user=active_user)

    summary = crud.metrics.get_activity_summary(db)

    assert summary.active_24h >= 1
    assert summary.active_7d >= summary.active_24h
    assert summary.active_30d >= summary.active_7d

    funnel = summary.funnel
    assert funnel.created_project >= 1
    # Each funnel stage is a subset of the one before it.
    assert (
        funnel.signed_up
        >= funnel.email_confirmed
        >= funnel.approved
        >= funnel.joined_project
        >= funnel.created_project
    )
    # Headline active-user total matches the approved + confirmed funnel stage.
    assert summary.total_users == funnel.approved


def test_get_activity_summary_counts_project_members_as_joined(db: Session) -> None:
    """A user added to someone else's project advances only the joined stage."""
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    member = create_user(db)

    before = crud.metrics.get_activity_summary(db).funnel
    create_project_member(
        db, member_id=member.id, project_uuid=project.id, role=Role.VIEWER
    )
    after = crud.metrics.get_activity_summary(db).funnel

    assert after.joined_project == before.joined_project + 1
    assert after.created_project == before.created_project


def test_get_activity_summary_ignores_deactivated_projects(db: Session) -> None:
    """Deactivating a project removes its owner from both project stages."""
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)

    before = crud.metrics.get_activity_summary(db).funnel
    crud.project.deactivate(db, project_id=project.id, user_id=owner.id)
    after = crud.metrics.get_activity_summary(db).funnel

    assert after.created_project == before.created_project - 1
    assert after.joined_project == before.joined_project - 1


def test_get_engagement_leaderboard_attributes_to_creator(db: Session) -> None:
    owner = create_user(db)
    # Two data products under the same project/flight owned by `owner`.
    sample = SampleDataProduct(db, user=owner)
    second = SampleDataProduct(
        db, user=owner, project=sample.project, flight=sample.flight
    )
    # Engagement received on the owner's data products.
    for _ in range(3):
        create_data_product_view(db, data_product_id=sample.obj.id)
    create_data_product_like(db, data_product_id=sample.obj.id)
    create_data_product_like(db, data_product_id=second.obj.id)

    rows = crud.metrics.get_engagement_leaderboard(
        db, metric="data_products", limit=100
    )
    owner_row = next(row for row in rows if row.user_id == owner.id)

    assert owner_row.name == owner.full_name
    assert owner_row.email == owner.email
    assert owner_row.project_count == 1
    assert owner_row.flight_count == 1
    assert owner_row.data_product_count == 2  # separate queries, not multiplied
    assert owner_row.total_views == 3
    assert owner_row.total_likes == 2


def test_get_engagement_leaderboard_orders_and_limits_by_metric(db: Session) -> None:
    popular = create_user(db)
    quiet = create_user(db)
    popular_dp = SampleDataProduct(db, user=popular)
    SampleDataProduct(db, user=quiet)
    for _ in range(5):
        create_data_product_view(db, data_product_id=popular_dp.obj.id)

    top = crud.metrics.get_engagement_leaderboard(db, metric="views", limit=1)

    assert len(top) == 1
    assert top[0].user_id == popular.id
    assert top[0].total_views == 5


def test_leaderboard_credits_flights_to_owner_not_pilot(db: Session) -> None:
    owner = create_user(db)
    pilot = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_flight(db, project_id=project.id, pilot_id=pilot.id)

    rows = crud.metrics.get_engagement_leaderboard(db, metric="flights", limit=100)
    owner_row = next((row for row in rows if row.user_id == owner.id), None)
    pilot_row = next((row for row in rows if row.user_id == pilot.id), None)

    assert owner_row is not None
    assert owner_row.flight_count == 1
    # The pilot owns nothing, so they are not credited for the flight.
    assert pilot_row is None


def test_leaderboard_data_usage_sums_data_products_and_raw_data(db: Session) -> None:
    owner = create_user(db)
    sample = SampleDataProduct(db, user=owner)
    raw = SampleRawData(db, user=owner, project=sample.project, flight=sample.flight)
    # Deterministic sizes via partial update (CRUDBase.update excludes unset).
    crud.data_product.update(
        db, db_obj=sample.obj, obj_in=DataProductUpdate(file_size=1000)
    )
    crud.raw_data.update(db, db_obj=raw.obj, obj_in=RawDataUpdate(file_size=500))

    rows = crud.metrics.get_engagement_leaderboard(db, metric="storage", limit=100)
    owner_row = next(row for row in rows if row.user_id == owner.id)

    assert owner_row.total_storage == 1500


def test_leaderboard_orders_by_data_usage(db: Session) -> None:
    heavy = create_user(db)
    light = create_user(db)
    heavy_dp = SampleDataProduct(db, user=heavy)
    light_dp = SampleDataProduct(db, user=light)
    crud.data_product.update(
        db, db_obj=heavy_dp.obj, obj_in=DataProductUpdate(file_size=10_000)
    )
    crud.data_product.update(
        db, db_obj=light_dp.obj, obj_in=DataProductUpdate(file_size=10)
    )

    top = crud.metrics.get_engagement_leaderboard(db, metric="storage", limit=1)

    assert len(top) == 1
    assert top[0].user_id == heavy.id
    assert top[0].total_storage == 10_000


def test_set_file_size_persists_on_disk_directory_size(db: Session) -> None:
    sample = SampleDataProduct(db)

    size = crud.data_product.set_file_size(db, sample.obj.id)

    assert size is not None
    assert size > 0
    refreshed = crud.data_product.get(db, id=sample.obj.id)
    assert refreshed.file_size == size


def test_create_activity_snapshot_is_idempotent_per_day(db: Session) -> None:
    active_user = create_user(db)
    crud.user.update_last_login(db, user=active_user)

    snapshot = crud.metrics.create_activity_snapshot(db)
    assert snapshot.snapshot_date == date.today()
    assert snapshot.active_24h >= 1
    assert snapshot.total_users >= 1
    original_id = snapshot.id

    # Re-running for the same day updates the existing row rather than inserting.
    rerun = crud.metrics.create_activity_snapshot(db)
    assert rerun.id == original_id

    trends = crud.metrics.get_activity_trends(db, days=7)
    today_points = [point for point in trends if point.snapshot_date == date.today()]
    assert len(today_points) == 1
    assert today_points[0].active_24h == rerun.active_24h


def test_get_activity_trends_computes_stickiness(db: Session) -> None:
    active_user = create_user(db)
    crud.user.update_last_login(db, user=active_user)
    crud.metrics.create_activity_snapshot(db)

    trends = crud.metrics.get_activity_trends(db, days=30)
    today_point = next(p for p in trends if p.snapshot_date == date.today())

    expected = round(today_point.active_24h / today_point.active_30d, 3)
    assert today_point.stickiness == expected


def test_leaderboard_excludes_engagement_on_deactivated_content(db: Session) -> None:
    """Views and likes on deactivated data products drop out, like every other
    leaderboard metric."""
    owner = create_user(db)
    live = SampleDataProduct(db, user=owner)
    removed = SampleDataProduct(
        db, user=owner, project=live.project, flight=live.flight
    )
    create_data_product_view(db, data_product_id=live.obj.id)
    create_data_product_view(db, data_product_id=removed.obj.id)
    create_data_product_like(db, data_product_id=live.obj.id)
    create_data_product_like(db, data_product_id=removed.obj.id)

    crud.data_product.deactivate(db, data_product_id=removed.obj.id)

    rows = crud.metrics.get_engagement_leaderboard(db, metric="views", limit=100)
    owner_row = next(row for row in rows if row.user_id == owner.id)

    assert owner_row.data_product_count == 1
    assert owner_row.total_views == 1
    assert owner_row.total_likes == 1
