from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.role import Role
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_like import create_data_product_like
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def _like_url(data_product: SampleDataProduct) -> str:
    return (
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}"
        f"/data_products/{data_product.obj.id}/like"
    )


def test_like_data_product_returns_201(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    response = client.post(_like_url(data_product))

    assert response.status_code == status.HTTP_201_CREATED


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
