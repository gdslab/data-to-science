import random
import string
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core import security
from app.core.config import settings
from app.tests.utils.user import create_random_user


def test_login_with_valid_credentials(client: TestClient, db: Session) -> None:
    user = create_random_user(db, password="mysecretpassword")
    data = {"username": user.email, "password": "mysecretpassword"}
    r = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data=data,
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    assert r.cookies.get("access_token")


def test_login_with_invalid_credentials(client: TestClient, db: Session) -> None:
    user = create_random_user(db, password="mysecretpassword")
    data = {"username": user.email, "password": "mywrongpassword"}
    r = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data=data,
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401
    assert r.cookies.get("access_token") is None


def test_logout_removes_authorization_cookie(client: TestClient, db: Session) -> None:
    user = create_random_user(db, password="mysecretpassword")
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
    user = create_random_user(db)
    expire = datetime.utcnow() + timedelta(minutes=1440)
    confirmation_token = security.create_access_token(user.id, expire=expire)
    r = client.get(
        f"{settings.API_V1_STR}/auth/confirm-email",
        params={"token": confirmation_token},
    )
    user_in_db = crud.user.get(db, id=user.id)
    assert r.request.url == settings.DOMAIN + "/auth/login?email_confirmed=true"
    assert user.is_email_confirmed is False
    assert user_in_db and user_in_db.is_email_confirmed is True


def test_email_confirmation_with_expired_token(client: TestClient, db: Session) -> None:
    user = create_random_user(db)
    expire = datetime.utcnow() - timedelta(minutes=5)
    confirmation_token = security.create_access_token(user.id, expire=expire)
    r = client.get(
        f"{settings.API_V1_STR}/auth/confirm-email",
        params={"token": confirmation_token},
    )
    user_in_db = crud.user.get(db, id=user.id)
    assert user_in_db and user_in_db.is_email_confirmed is False
    assert r.status_code == 403


def test_email_confirmation_with_invalid_token(client: TestClient, db: Session) -> None:
    user = create_random_user(db)
    expire = datetime.utcnow() + timedelta(minutes=1440)
    confirmation_token = security.create_access_token(user.id, expire=expire)
    junk = "".join(random.choices(string.ascii_letters + string.digits, k=5))
    confirmation_token = confirmation_token[:-5] + junk
    r = client.get(
        f"{settings.API_V1_STR}/auth/confirm-email",
        params={"token": confirmation_token},
    )
    user_in_db = crud.user.get(db, id=user.id)
    assert user_in_db and user_in_db.is_email_confirmed is False
    assert r.status_code == 403
