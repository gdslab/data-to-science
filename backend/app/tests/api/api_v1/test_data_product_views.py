from datetime import datetime, timedelta, timezone

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.data_product_view import DataProductView
from app.schemas.file_permission import FilePermissionUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_view import create_data_product_view
from app.tests.utils.flight import create_flight
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user


def _view_url(data_product: SampleDataProduct) -> str:
    return (
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}"
        f"/data_products/{data_product.obj.id}/view"
    )


def _public_view_url(data_product: SampleDataProduct) -> str:
    return f"{settings.API_V1_STR}/public/data_products/{data_product.obj.id}/view"


# ── Authenticated view endpoint ──────────────────────────────────────────────


def test_authenticated_view_returns_201(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    response = client.post(_view_url(data_product))

    assert response.status_code == status.HTTP_201_CREATED


def test_authenticated_view_within_window_returns_200(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    client.post(_view_url(data_product))
    response = client.post(_view_url(data_product))

    assert response.status_code == status.HTTP_200_OK


def test_authenticated_view_after_window_returns_201(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    old_time = datetime.now(tz=timezone.utc) - timedelta(hours=2)

    create_data_product_view(
        db,
        data_product_id=data_product.obj.id,
        user_id=current_user.id,
        viewed_at=old_time,
    )
    response = client.post(_view_url(data_product))

    assert response.status_code == status.HTTP_201_CREATED


def test_authenticated_view_with_mismatched_flight_returns_403(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # IDOR guard: a flight the user owns in the path must not allow recording a
    # view against a data product that belongs to a different flight.
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    other_flight = create_flight(db, project_id=data_product.project.id)
    url = (
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{other_flight.id}"
        f"/data_products/{data_product.obj.id}/view"
    )

    response = client.post(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


# ── Public anonymous view endpoint ───────────────────────────────────────────


def _make_published(db: Session, data_product: SampleDataProduct) -> None:
    """Publish the data product's project."""
    crud.project.update_project_visibility(
        db, project_id=data_product.project.id, is_public=True
    )


def _make_file_public(db: Session, data_product: SampleDataProduct) -> None:
    """Mark the data product's file permission as public (shared link)."""
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product.obj.id
    )
    assert file_permission
    crud.file_permission.update(
        db, db_obj=file_permission, obj_in=FilePermissionUpdate(is_public=True)
    )


def test_public_view_session_id_too_long_returns_422(
    client: TestClient, db: Session
) -> None:
    # An over-length header is rejected before the DB call (no String(64) DataError/500).
    data_product = SampleDataProduct(db)
    _make_published(db, data_product)

    response = client.post(
        _public_view_url(data_product),
        headers={"X-Session-Id": "x" * 65},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_public_view_session_id_at_max_length_returns_201(
    client: TestClient, db: Session
) -> None:
    data_product = SampleDataProduct(db)
    _make_published(db, data_product)

    response = client.post(
        _public_view_url(data_product),
        headers={"X-Session-Id": "x" * 64},
    )

    assert response.status_code == status.HTTP_201_CREATED


def test_public_anonymous_view_with_session_id_returns_201(
    client: TestClient, db: Session
) -> None:
    data_product = SampleDataProduct(db)
    _make_published(db, data_product)

    response = client.post(
        _public_view_url(data_product),
        headers={"X-Session-Id": "test-session-001"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"view_count": 1}


def test_public_anonymous_view_without_session_id_returns_400(
    client: TestClient, db: Session
) -> None:
    data_product = SampleDataProduct(db)
    _make_published(db, data_product)

    response = client.post(_public_view_url(data_product))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_public_view_on_unpublished_project_returns_404(
    client: TestClient, db: Session
) -> None:
    data_product = SampleDataProduct(db)

    response = client.post(
        _public_view_url(data_product),
        headers={"X-Session-Id": "test-session-002"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_public_view_anonymous_file_public_unpublished_returns_201(
    client: TestClient, db: Session
) -> None:
    # Shared-link access model: a public file permission must allow view
    # recording even when the project itself is not published.
    data_product = SampleDataProduct(db)
    _make_file_public(db, data_product)

    response = client.post(
        _public_view_url(data_product),
        headers={"X-Session-Id": "test-session-share"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"view_count": 1}


def test_public_view_dedup_same_session_returns_200(
    client: TestClient, db: Session
) -> None:
    data_product = SampleDataProduct(db)
    _make_published(db, data_product)

    client.post(
        _public_view_url(data_product),
        headers={"X-Session-Id": "test-session-003"},
    )
    response = client.post(
        _public_view_url(data_product),
        headers={"X-Session-Id": "test-session-003"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"view_count": 1}


def test_public_view_different_sessions_both_count(
    client: TestClient, db: Session
) -> None:
    data_product = SampleDataProduct(db)
    _make_published(db, data_product)

    client.post(
        _public_view_url(data_product), headers={"X-Session-Id": "session-A"}
    )
    client.post(
        _public_view_url(data_product), headers={"X-Session-Id": "session-B"}
    )

    count = crud.data_product_view.get_count_by_data_product_id(
        db, data_product_id=data_product.obj.id
    )
    assert count == 2


# ── Public view endpoint — signed-in callers ─────────────────────────────────
# The TestClient persists the access_token cookie set by the
# normal_user_access_token fixture, so requests below are authenticated as the
# normal user. The public endpoint reads that cookie via get_optional_current_user.


def test_public_view_signed_in_member_unpublished_returns_201(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    # Data product owned by the current user, project left unpublished.
    data_product = SampleDataProduct(db, user=current_user)

    response = client.post(_public_view_url(data_product))

    assert response.status_code == status.HTTP_201_CREATED
    view = db.scalar(
        select(DataProductView).where(
            DataProductView.data_product_id == data_product.obj.id
        )
    )
    assert view is not None
    assert view.user_id == current_user.id
    assert view.session_id is None


def test_public_view_signed_in_non_member_unpublished_returns_404(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Data product owned by a different user; current user is not a member.
    data_product = SampleDataProduct(db)

    response = client.post(_public_view_url(data_product))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    count = crud.data_product_view.get_count_by_data_product_id(
        db, data_product_id=data_product.obj.id
    )
    assert count == 0


def test_public_view_signed_in_non_member_file_public_unpublished_returns_201(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Shared-link access model: signed-in non-members can record views on a
    # publicly shared file in an unpublished project.
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    _make_file_public(db, data_product)

    response = client.post(_public_view_url(data_product))

    assert response.status_code == status.HTTP_201_CREATED
    view = db.scalar(
        select(DataProductView).where(
            DataProductView.data_product_id == data_product.obj.id
        )
    )
    assert view is not None
    assert view.user_id == current_user.id


def test_public_view_signed_in_non_member_published_returns_201(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Published project owned by another user; current user is not a member.
    data_product = SampleDataProduct(db)
    _make_published(db, data_product)

    response = client.post(_public_view_url(data_product))

    assert response.status_code == status.HTTP_201_CREATED
