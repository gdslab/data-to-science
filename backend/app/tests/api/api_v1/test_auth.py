import random
import secrets
import string

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.user import create_user


def test_login_with_valid_credentials(client: TestClient, db: Session) -> None:
    user = create_user(db, password="mysecretpassword")
    data = {"username": user.email, "password": "mysecretpassword"}
    r = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data=data,
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    assert r.cookies.get("access_token")


def test_login_with_email_in_different_case(client: TestClient, db: Session) -> None:
    user = create_user(db, password="mysecretpassword")
    data = {"username": user.email.upper(), "password": "mysecretpassword"}
    assert user.email != user.email.upper()
    r = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data=data,
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    assert r.cookies.get("access_token")


def test_login_with_invalid_credentials(client: TestClient, db: Session) -> None:
    user = create_user(db, password="mysecretpassword")
    data = {"username": user.email, "password": "mywrongpassword"}
    r = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data=data,
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401
    assert r.cookies.get("access_token") is None


def test_logout_removes_authorization_cookie(client: TestClient, db: Session) -> None:
    user = create_user(db, password="mysecretpassword")
    data = {"username": user.email, "password": "mysecretpassword"}
    # login
    r = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data=data,
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    assert r.cookies.get("access_token")
    assert client.cookies.get("access_token")
    # logout
    r = client.get(f"{settings.API_V1_STR}/auth/remove-access-token")
    assert r.status_code == 200
    assert r.cookies.get("access_token") is None
    assert client.cookies.get("access_token") is None


def test_email_confirmation_with_valid_token(client: TestClient, db: Session) -> None:
    token = secrets.token_urlsafe()
    user = create_user(db, token=token)
    r = client.get(
        f"{settings.API_V1_STR}/auth/confirm-email",
        params={"token": token},
    )
    user_in_db = crud.user.get(db, id=user.id)
    assert r.request.url == settings.API_DOMAIN + "/auth/login?email_confirmed=true"
    assert user.is_email_confirmed is False
    assert user_in_db and user_in_db.is_email_confirmed is True


# def test_email_confirmation_with_expired_token(
#     client: TestClient,
#     db: Session
# ) -> None:
#     token = secrets.token_urlsafe()
#     user = create_user(db, token=token, token_expired=True)
#     r = client.get(
#         f"{settings.API_V1_STR}/auth/confirm-email",
#         params={"token": token},
#     )
#     user_in_db = crud.user.get(db, id=user.id)
#     assert user_in_db and user_in_db.is_email_confirmed is False
#     assert r.status_code == 403


def test_change_password(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    data = {
        "current_password": "testuserpassword",
        "new_password": "new-testuserpassword",
    }
    response = client.post(f"{settings.API_V1_STR}/auth/change-password", data=data)
    assert response.status_code == status.HTTP_200_OK
    # login with new credentials
    login_data = {"username": current_user.email, "password": "new-testuserpassword"}
    r = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data=login_data,
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    assert r.cookies.get("access_token")


def test_email_confirmation_with_invalid_token(client: TestClient, db: Session) -> None:
    token = secrets.token_urlsafe()
    user = create_user(db, token=token)
    junk = "".join(random.choices(string.ascii_letters + string.digits, k=5))
    r = client.get(
        f"{settings.API_V1_STR}/auth/confirm-email",
        params={"token": token[:-5] + junk},
    )
    user_in_db = crud.user.get(db, id=user.id)
    assert user_in_db and user_in_db.is_email_confirmed is False
    assert r.request.url == settings.API_DOMAIN + "/auth/login?error=invalid"
