from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app import crud
from app.schemas.role import Role
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_like import create_data_product_like
from app.tests.utils.data_product_view import create_data_product_view
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def _current_week_start() -> datetime:
    today = datetime.now(tz=timezone.utc).date()
    return today - timedelta(days=today.weekday())


def test_get_owner_stats_counts_only_owned_products(db: Session) -> None:
    owner_sample = SampleDataProduct(db)
    other_sample = SampleDataProduct(db)

    create_data_product_view(
        db, data_product_id=owner_sample.obj.id, user_id=create_user(db).id
    )
    create_data_product_view(
        db, data_product_id=owner_sample.obj.id, session_id="anon-session"
    )
    create_data_product_like(db, data_product_id=owner_sample.obj.id)
    # Activity on a product owned by someone else must not be counted.
    create_data_product_view(
        db, data_product_id=other_sample.obj.id, user_id=create_user(db).id
    )
    create_data_product_like(db, data_product_id=other_sample.obj.id)

    stats = crud.data_product.get_owner_stats(db, user_id=owner_sample.user.id)

    assert stats["total_views"] == 2
    assert stats["total_likes"] == 1
    assert stats["data_product_count"] == 1
    assert stats["project_count"] == 1
    assert stats["public_count"] == 0


def test_get_owner_stats_includes_co_owner_projects(db: Session) -> None:
    # A member promoted to the OWNER role (not the project creator) should see
    # the co-owned project's data in their stats.
    sample = SampleDataProduct(db)
    co_owner = create_user(db)
    create_project_member(
        db,
        role=Role.OWNER,
        member_id=co_owner.id,
        project_uuid=sample.project.id,
    )
    create_data_product_view(
        db, data_product_id=sample.obj.id, session_id="anon-co-owner"
    )

    co_owner_stats = crud.data_product.get_owner_stats(db, user_id=co_owner.id)
    creator_stats = crud.data_product.get_owner_stats(db, user_id=sample.user.id)

    # Both owners see the same shared project's data (not split between them).
    assert co_owner_stats["data_product_count"] == 1
    assert co_owner_stats["project_count"] == 1
    assert co_owner_stats["total_views"] == 1
    assert creator_stats["data_product_count"] == 1
    assert creator_stats["total_views"] == 1


def test_get_owner_stats_excludes_non_owner_members(db: Session) -> None:
    # A viewer/manager member who is NOT an owner should not see the project's
    # data in their "On your data" stats.
    sample = SampleDataProduct(db)
    viewer = create_user(db)
    create_project_member(
        db,
        role=Role.VIEWER,
        member_id=viewer.id,
        project_uuid=sample.project.id,
    )
    create_data_product_view(
        db, data_product_id=sample.obj.id, session_id="anon-viewer"
    )

    stats = crud.data_product.get_owner_stats(db, user_id=viewer.id)

    assert stats["data_product_count"] == 0
    assert stats["project_count"] == 0
    assert stats["total_views"] == 0


def test_get_owner_stats_includes_anonymous_views(db: Session) -> None:
    sample = SampleDataProduct(db)

    create_data_product_view(
        db, data_product_id=sample.obj.id, session_id="anon-session-1"
    )
    create_data_product_view(
        db, data_product_id=sample.obj.id, session_id="anon-session-2"
    )

    stats = crud.data_product.get_owner_stats(db, user_id=sample.user.id)

    assert stats["total_views"] == 2


def test_get_owner_stats_public_count_reflects_visibility(db: Session) -> None:
    sample = SampleDataProduct(db)

    crud.project.update_project_visibility(
        db, project_id=sample.project.id, is_public=True
    )

    stats = crud.data_product.get_owner_stats(db, user_id=sample.user.id)

    assert stats["public_count"] == 1


def test_get_owner_stats_with_no_data_returns_zeros(db: Session) -> None:
    user = create_user(db)

    stats = crud.data_product.get_owner_stats(db, user_id=user.id)

    assert stats == {
        "total_views": 0,
        "total_likes": 0,
        "data_product_count": 0,
        "public_count": 0,
        "project_count": 0,
    }


def test_get_owner_views_trend_is_zero_filled(db: Session) -> None:
    sample = SampleDataProduct(db)

    points = crud.data_product.get_owner_views_trend(
        db, user_id=sample.user.id, weeks=12
    )

    assert len(points) == 12
    assert all(point["views"] == 0 for point in points)
    assert points[-1]["week_start"] == _current_week_start().isoformat()


def test_get_owner_views_trend_buckets_by_week(db: Session) -> None:
    sample = SampleDataProduct(db)
    current_week_start = _current_week_start()
    last_week_view_time = datetime.combine(
        current_week_start - timedelta(weeks=1), datetime.min.time()
    ).replace(tzinfo=timezone.utc) + timedelta(hours=1)

    create_data_product_view(
        db,
        data_product_id=sample.obj.id,
        session_id="anon-this-week",
    )
    create_data_product_view(
        db,
        data_product_id=sample.obj.id,
        session_id="anon-last-week",
        viewed_at=last_week_view_time,
    )

    points = crud.data_product.get_owner_views_trend(
        db, user_id=sample.user.id, weeks=12
    )
    points_by_week = {point["week_start"]: point["views"] for point in points}

    assert points_by_week[current_week_start.isoformat()] == 1
    assert (
        points_by_week[(current_week_start - timedelta(weeks=1)).isoformat()] == 1
    )


def test_get_owner_top_orders_by_requested_metric(db: Session) -> None:
    owner = create_user(db)
    project = SampleDataProduct(db, user=owner)
    more_viewed = SampleDataProduct(db, user=owner, project=project.project)
    more_liked = SampleDataProduct(db, user=owner, project=project.project)

    create_data_product_view(
        db, data_product_id=more_viewed.obj.id, session_id="s1"
    )
    create_data_product_view(
        db, data_product_id=more_viewed.obj.id, session_id="s2"
    )
    create_data_product_like(db, data_product_id=more_liked.obj.id)
    create_data_product_like(
        db, data_product_id=more_liked.obj.id, user_id=create_user(db).id
    )

    top_by_views = crud.data_product.get_owner_top(
        db, user_id=owner.id, metric="views", limit=5
    )
    top_by_likes = crud.data_product.get_owner_top(
        db, user_id=owner.id, metric="likes", limit=5
    )

    assert top_by_views[0]["id"] == more_viewed.obj.id
    assert top_by_views[0]["views"] == 2
    assert top_by_likes[0]["id"] == more_liked.obj.id
    assert top_by_likes[0]["likes"] == 2


def test_get_owner_top_respects_limit(db: Session) -> None:
    owner = create_user(db)
    project = SampleDataProduct(db, user=owner).project
    for _ in range(3):
        SampleDataProduct(db, user=owner, project=project)

    top = crud.data_product.get_owner_top(db, user_id=owner.id, limit=2)

    assert len(top) == 2


def test_get_activity_counts_are_distinct_products(db: Session) -> None:
    user = create_user(db)
    sample_a = SampleDataProduct(db)
    sample_b = SampleDataProduct(db)

    # Two views of the same product (different sessions to avoid dedup) should
    # still count as one viewed product.
    create_data_product_view(db, data_product_id=sample_a.obj.id, user_id=user.id)
    create_data_product_view(
        db, data_product_id=sample_a.obj.id, session_id="anon-other-session"
    )
    create_data_product_view(db, data_product_id=sample_b.obj.id, user_id=user.id)
    create_data_product_like(db, data_product_id=sample_a.obj.id, user_id=user.id)

    counts = crud.data_product.get_activity_counts(db, user_id=user.id)

    assert counts == {"viewed_count": 2, "liked_count": 1}


def test_get_recent_activity_viewed_orders_by_recency(db: Session) -> None:
    user = create_user(db)
    older = SampleDataProduct(db)
    newer = SampleDataProduct(db)
    now = datetime.now(tz=timezone.utc)

    create_data_product_view(
        db,
        data_product_id=older.obj.id,
        user_id=user.id,
        viewed_at=now - timedelta(days=2),
    )
    create_data_product_view(
        db,
        data_product_id=newer.obj.id,
        user_id=user.id,
        viewed_at=now - timedelta(hours=1),
    )

    recent = crud.data_product.get_recent_activity(
        db, user_id=user.id, action="viewed", limit=3
    )

    assert recent[0]["id"] == newer.obj.id
    assert recent[0]["owner_name"] == f"{newer.user.first_name} {newer.user.last_name}"
    assert recent[1]["id"] == older.obj.id


def test_get_recent_activity_liked_orders_by_recency(db: Session) -> None:
    user = create_user(db)
    older = SampleDataProduct(db)
    newer = SampleDataProduct(db)

    create_data_product_like(db, data_product_id=older.obj.id, user_id=user.id)
    create_data_product_like(db, data_product_id=newer.obj.id, user_id=user.id)

    recent = crud.data_product.get_recent_activity(
        db, user_id=user.id, action="liked", limit=3
    )

    assert recent[0]["id"] == newer.obj.id
    assert recent[1]["id"] == older.obj.id


def test_get_recent_activity_respects_limit(db: Session) -> None:
    user = create_user(db)
    for _ in range(4):
        sample = SampleDataProduct(db)
        create_data_product_view(db, data_product_id=sample.obj.id, user_id=user.id)

    recent = crud.data_product.get_recent_activity(
        db, user_id=user.id, action="viewed", limit=2
    )

    assert len(recent) == 2
