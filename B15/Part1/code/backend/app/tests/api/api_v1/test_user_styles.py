from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.user_style import UserStyleUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.DefaultUserStyle import DefaultUserStyle


def test_create_data_product_user_style(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=False, user=current_user)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/style",
        json={"settings": DefaultUserStyle().__dict__},
    )

    assert 201 == response.status_code
    response_user_style = response.json()
    assert response_user_style["data_product_id"] == str(data_product.obj.id)
    assert response_user_style["user_id"] == str(data_product.user.id)
    assert response_user_style["settings"]["min"] == 0  # default is 0
    assert response_user_style["settings"]["max"] == 255  # default is 255


def test_update_data_product_user_style(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, create_style=True, user=current_user)
    user_style_settings = data_product.user_style.settings
    user_style_settings.update({"min": 25, "max": 50})
    updated_user_style_in = UserStyleUpdate(settings=user_style_settings)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/style",
        json=updated_user_style_in.model_dump(),
    )

    assert 200 == response.status_code
    response_user_style = response.json()
    assert response_user_style["data_product_id"] == str(data_product.obj.id)
    assert response_user_style["user_id"] == str(data_product.user.id)
    assert response_user_style["settings"]["min"] == 25  # default is 0
    assert response_user_style["settings"]["max"] == 50  # default is 255
