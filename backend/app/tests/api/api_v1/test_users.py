from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.user import UserUpdate
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_email, random_full_name, random_password


def test_create_user_new_email(client: TestClient, db: Session) -> None:
    """Verify new user is created in database."""
    full_name = random_full_name()
    data = {
        "email": random_email(),
        "password": random_password(),
        "first_name": full_name["first"],
        "last_name": full_name["last"],
    }
    r = client.post(f"{settings.API_V1_STR}/users/", json=data)
    assert 201 == r.status_code
    created_user = r.json()
    user = crud.user.get_by_email(db, email=data["email"])
    assert user
    assert user.email == created_user["email"]


def test_create_user_existing_email(client: TestClient, db: Session) -> None:
    """Verify new user is not created in database when existing email provided."""
    existing_user = create_random_user(db, email=random_email())
    data = {
        "email": existing_user.email,
        "password": random_password(),
        "first_name": existing_user.first_name,
        "last_name": existing_user.last_name,
    }
    r = client.post(f"{settings.API_V1_STR}/users/", json=data)
    assert 400 == r.status_code


def test_get_users_normal_current_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify normal user can be retrieved with JWT token."""
    r = client.get(
        f"{settings.API_V1_STR}/users/current", headers=normal_user_token_headers
    )
    current_user = r.json()
    assert current_user
    assert settings.EMAIL_TEST_USER == current_user["email"]


def test_update_user(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify update changes user attributes in database."""
    current_user = get_current_user(
        db, normal_user_token_headers["Authorization"].split(" ")[1]
    )
    full_name = random_full_name()
    user_in = UserUpdate(
        first_name=full_name["first"],
        last_name=full_name["last"],
    )
    r = client.put(
        f"{settings.API_V1_STR}/users/{current_user.id}",
        json=user_in.dict(),
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    updated_user = r.json()
    assert updated_user
    assert str(current_user.id) == updated_user["id"]
    assert full_name["first"] == updated_user["first_name"]
    assert full_name["last"] == updated_user["last_name"]
