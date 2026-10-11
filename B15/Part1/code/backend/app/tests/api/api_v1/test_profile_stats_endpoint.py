from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_like import create_data_product_like
from app.tests.utils.data_product_view import create_data_product_view

STATS_URL = f"{settings.API_V1_STR}/users/current/stats"


def test_get_current_user_stats_requires_authentication(client: TestClient) -> None:
    response = client.get(STATS_URL, headers={"Authorization": ""})

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


def test_get_current_user_stats_shape_with_no_data(
    client: TestClient, normal_user_access_token: str
) -> None:
    response = client.get(STATS_URL)

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["received"] == {
        "total_views": 0,
        "total_likes": 0,
        "data_product_count": 0,
        "public_count": 0,
        "project_count": 0,
        "views_trend": body["received"]["views_trend"],
        "top_viewed": [],
        "top_liked": [],
    }
    assert len(body["received"]["views_trend"]) == 12
    assert body["activity"] == {
        "viewed_count": 0,
        "liked_count": 0,
        "recently_viewed": [],
        "recently_liked": [],
    }


def test_get_current_user_stats_reflects_owned_and_personal_activity(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    owned_product = SampleDataProduct(db, user=current_user)
    other_product = SampleDataProduct(db)

    # Engagement on the user's own data (owner side).
    create_data_product_view(
        db, data_product_id=owned_product.obj.id, session_id="anon-1"
    )
    create_data_product_like(db, data_product_id=owned_product.obj.id)

    # The user's own activity elsewhere (activity side).
    create_data_product_view(
        db, data_product_id=other_product.obj.id, user_id=current_user.id
    )
    create_data_product_like(
        db, data_product_id=other_product.obj.id, user_id=current_user.id
    )

    response = client.get(STATS_URL)

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["received"]["total_views"] == 1
    assert body["received"]["total_likes"] == 1
    assert body["received"]["data_product_count"] == 1
    assert body["received"]["top_viewed"][0]["id"] == str(owned_product.obj.id)
    assert body["activity"]["viewed_count"] == 1
    assert body["activity"]["liked_count"] == 1
    assert body["activity"]["recently_viewed"][0]["id"] == str(other_product.obj.id)
    assert body["activity"]["recently_liked"][0]["id"] == str(other_product.obj.id)
