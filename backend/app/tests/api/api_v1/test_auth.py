import random
import secrets
import string
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from jose import jwt

from app import crud
from app.api.deps import get_current_user
from app.core import security
from app.core.config import settings
from app.schemas.refresh_token import RefreshTokenCreate
from app.schemas.user import UserUpdate
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


def test_change_password_with_demo_user(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    crud.user.update(db, db_obj=current_user, obj_in=UserUpdate(is_demo=True))
    data = {
        "current_password": "testuserpassword",
        "new_password": "new-testuserpassword",
    }
    response = client.post(f"{settings.API_V1_STR}/auth/change-password", data=data)
    assert response.status_code == 403


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


def test_refresh_token_success(client: TestClient, db: Session) -> None:
    """Test successful refresh token flow."""
    user = create_user(db, password="mysecretpassword")

    # First login to get refresh token
    data = {"username": user.email, "password": "mysecretpassword"}
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data=data,
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200

    # Extract refresh token from login response cookies
    refresh_token = login_response.cookies.get("refresh_token")
    assert refresh_token is not None

    # Use refresh token to get new tokens
    refresh_response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200
    response_data = refresh_response.json()

    # Verify response structure
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert response_data["token_type"] == "bearer"
    assert "expires_in" in response_data

    # Verify new cookies are set
    assert refresh_response.cookies.get("access_token") is not None
    assert refresh_response.cookies.get("refresh_token") is not None


def test_refresh_token_missing(client: TestClient, db: Session) -> None:
    """Test refresh token endpoint with missing token."""
    response = client.post(f"{settings.API_V1_STR}/auth/refresh-token")

    assert response.status_code == 401
    assert "Refresh token missing or malformed" in response.json()["detail"]


def test_refresh_token_malformed(client: TestClient, db: Session) -> None:
    """Test refresh token endpoint with malformed token."""
    # Test without Bearer prefix
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": "invalid-token-format"},
    )

    assert response.status_code == 401
    assert "Refresh token missing or malformed" in response.json()["detail"]


def test_refresh_token_invalid_jwt(client: TestClient, db: Session) -> None:
    """Test refresh token endpoint with invalid JWT."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": "Bearer invalid.jwt.token"},
    )

    assert response.status_code == 401
    # Should fail during JWT validation


def test_refresh_token_missing_jti(client: TestClient, db: Session) -> None:
    """Test refresh token endpoint with token missing JTI claim."""
    user = create_user(db)

    # Create a token without JTI
    payload = {
        "sub": str(user.id),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
        "iat": datetime.now(timezone.utc),
    }

    invalid_token = jwt.encode(
        payload, settings.SECRET_KEY, algorithm=security.ALGORITHM
    )

    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": f"Bearer {invalid_token}"},
    )

    assert response.status_code == 401
    assert "Refresh token payload missing jti" in response.json()["detail"]


def test_refresh_token_revoked(client: TestClient, db: Session) -> None:
    """Test refresh token endpoint with revoked token."""
    user = create_user(db)

    # Create a refresh token
    refresh_token_str = security.create_refresh_token(db, subject=str(user.id))

    # Decode to get JTI and revoke the token
    payload = security.decode_token(refresh_token_str)
    jti = payload["jti"]
    crud.refresh_token.revoke(db, jti=jti)

    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": f"Bearer {refresh_token_str}"},
    )

    assert response.status_code == 401
    assert "Refresh token revoked or expired" in response.json()["detail"]


def test_refresh_token_nonexistent_in_db(client: TestClient, db: Session) -> None:
    """Test refresh token endpoint with token not in database."""
    user = create_user(db)

    # Create a token with random JTI that doesn't exist in DB
    payload = {
        "sub": str(user.id),
        "jti": str(uuid4()),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
        "iat": datetime.now(timezone.utc),
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=security.ALGORITHM)

    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert "Refresh token revoked or expired" in response.json()["detail"]


def test_refresh_token_expired_in_db(client: TestClient, db: Session) -> None:
    """Test refresh token endpoint with token expired in database."""
    user = create_user(db)

    # Create an expired refresh token in the database
    now = datetime.now(timezone.utc)
    expired_time = now - timedelta(days=1)
    token_jti = uuid4()
    refresh_token_create = RefreshTokenCreate(
        jti=token_jti,
        user_id=user.id,
        issued_at=expired_time - timedelta(days=30),  # Issued 31 days ago
        expires_at=expired_time,  # Expired yesterday
    )
    db_token = crud.refresh_token.create(db, obj_in=refresh_token_create)

    # Create JWT with matching JTI
    payload = {
        "sub": str(user.id),
        "jti": str(token_jti),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=1),  # JWT itself not expired
        "iat": datetime.now(timezone.utc),
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=security.ALGORITHM)

    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert "Refresh token revoked or expired" in response.json()["detail"]


def test_refresh_token_revokes_old_token(client: TestClient, db: Session) -> None:
    """Test that refresh token endpoint revokes the old token."""
    user = create_user(db)

    # Create a refresh token
    refresh_token_str = security.create_refresh_token(db, subject=str(user.id))
    payload = security.decode_token(refresh_token_str)
    jti = payload["jti"]

    # Verify token is not revoked initially
    db_token_before = crud.refresh_token.get_by_jti(db, jti=jti)
    assert db_token_before is not None
    assert not db_token_before.revoked

    # Use refresh token
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": f"Bearer {refresh_token_str}"},
    )

    assert response.status_code == 200

    # Verify old token is revoked
    db_token_after = crud.refresh_token.get_by_jti(db, jti=jti)
    assert db_token_after is not None
    assert db_token_after.revoked
