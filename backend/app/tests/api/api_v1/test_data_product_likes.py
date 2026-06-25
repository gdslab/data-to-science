from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.models import Flight, Project
from app.schemas.role import Role
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_like import create_data_product_like
from app.tests.utils.flight import create_flight
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def _like_url(data_product: SampleDataProduct) -> str:
    return (
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}"
        f"/data_products/{data_product.obj.id}/like"
    )


def test_like_with_mismatched_flight_returns_403(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # IDOR guard: passing a flight the user owns must not allow liking a data
    # product that belongs to a different flight.
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    other_flight = create_flight(db, project_id=data_product.project.id)
    url = (
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{other_flight.id}"
        f"/data_products/{data_product.obj.id}/like"
    )

    response = client.post(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_concurrent_like_returns_400_not_500(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    monkeypatch,
) -> None:
    # Simulate a race: a like already exists, but the pre-check misses it, so the
    # insert hits the unique constraint. Expect a graceful 400, not a 500.
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    create_data_product_like(
        db, data_product_id=data_product.obj.id, user_id=current_user.id
    )
    monkeypatch.setattr(
        crud.data_product_like,
        "get_by_data_product_id_and_user_id",
        lambda *args, **kwargs: None,
    )

    response = client.post(_like_url(data_product))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_like_data_product_returns_201(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    response = client.post(_like_url(data_product))

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"liked": True, "like_count": 1}


def test_like_returns_total_like_count(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    # A like from another user already exists
    other_user = create_user(db)
    create_data_product_like(
        db, data_product_id=data_product.obj.id, user_id=other_user.id
    )

    response = client.post(_like_url(data_product))

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"liked": True, "like_count": 2}


def test_duplicate_like_returns_400(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    client.post(_like_url(data_product))
    response = client.post(_like_url(data_product))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_unlike_data_product_returns_200(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    create_data_product_like(
        db, data_product_id=data_product.obj.id, user_id=current_user.id
    )

    response = client.delete(_like_url(data_product))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"liked": False, "like_count": 0}


def test_unlike_not_liked_returns_400(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    response = client.delete(_like_url(data_product))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_like_requires_authentication(
    client: TestClient, db: Session
) -> None:
    data_product = SampleDataProduct(db)

    response = client.post(
        _like_url(data_product), headers={"Authorization": ""}
    )

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


def test_like_denied_for_non_member(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # data_product owned by a different user; current_user is not a member.
    # can_read_project returns 404 when the authenticated user has no project membership.
    data_product = SampleDataProduct(db)

    response = client.post(_like_url(data_product))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_like_allowed_for_non_member_when_public(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Any authenticated user can like a data product in a published/public
    # project, even without project membership.
    data_product = SampleDataProduct(db)
    crud.project.update_project_visibility(
        db, project_id=data_product.project.id, is_public=True
    )

    response = client.post(_like_url(data_product))

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"liked": True, "like_count": 1}


def test_unlike_allowed_for_non_member_when_public(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    crud.project.update_project_visibility(
        db, project_id=data_product.project.id, is_public=True
    )
    create_data_product_like(
        db, data_product_id=data_product.obj.id, user_id=current_user.id
    )

    response = client.delete(_like_url(data_product))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"liked": False, "like_count": 0}


def test_like_on_deactivated_flight_returns_404(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    # Defensive guard: a desync where the data product stays active but its
    # parent flight is deactivated must not allow engagement.
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    db.execute(
        update(Flight)
        .where(Flight.id == data_product.flight.id)
        .values(is_active=False)
    )
    db.commit()

    response = client.post(_like_url(data_product))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_like_on_deactivated_project_returns_404(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    db.execute(
        update(Project)
        .where(Project.id == data_product.project.id)
        .values(is_active=False)
    )
    db.commit()

    response = client.post(_like_url(data_product))

    assert response.status_code == status.HTTP_404_NOT_FOUND
