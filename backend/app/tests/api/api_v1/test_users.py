from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.user import UserCreate, UserUpdate
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_email, random_full_name, random_password


def test_create_user_new_email(client: TestClient, db: Session) -> None:
    """Test creating a new user account."""
    full_name = random_full_name()
    data = {
        "email": random_email(),
        "password": random_password(),
        "first_name": full_name["first"],
        "last_name": full_name["last"],
    }
    r = client.post(f"{settings.API_V1_STR}/users/", json=data)
    assert r.status_code == 201
    created_user = r.json()
    user = crud.user.get_by_email(db, email=data["email"])
    assert user
    assert user.email == created_user["email"]


def test_create_user_existing_email(client: TestClient, db: Session) -> None:
    """Test creating a new user account with an existing email."""
    existing_email = random_email()
    existing_user = create_random_user(db, existing_email)

    password = random_password()
    full_name = random_full_name()
    data = {
        "email": existing_email,
        "password": password,
        "first_name": full_name["first"],
        "last_name": full_name["last"],
    }
    r = client.post(f"{settings.API_V1_STR}/users/", json=data)
    assert 400 <= r.status_code < 500


def test_get_users_normal_current_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test retrieving current user using normal user token headers."""
    r = client.get(f"{settings.API_V1_STR}/users/current", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["email"] == settings.EMAIL_TEST_USER


def test_get_current_user_when_not_authorized(client: TestClient, db: Session) -> None:
    """Test retrieiving current user when the client is not authorized."""
    r = client.get(f"{settings.API_V1_STR}/users/")
    assert 400 <= r.status_code < 500


def test_update_user(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Test updating current user."""
    current_user = get_current_user(db, normal_user_token_headers["Authorization"].split(" ")[1])
    full_name = random_full_name()
    user_in = UserUpdate(
        first_name=full_name["first"],
        last_name=full_name["last"],
    )
    
    r = client.put(f"{settings.API_V1_STR}/users/{current_user.id}", json=user_in.dict(), headers=normal_user_token_headers)
    
    assert 200 <= r.status_code < 300
    updated_user = r.json()
    assert updated_user
    assert current_user.id == updated_user["id"]
    assert full_name["first"] == updated_user["first_name"]
    assert full_name["last"] == updated_user["last_name"]
