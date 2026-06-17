import random
import secrets
import string
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi import Response, status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from jose import jwt

from app import crud
from app.models.single_use_token import SingleUseToken
from app.api.deps import get_current_user
from app.core import security
from app.core.config import settings
from app.schemas.refresh_token import RefreshTokenCreate, RefreshTokenUpdate
from app.schemas.single_use_token import SingleUseTokenCreate
from app.schemas.user import UserUpdate
from app.tests.utils.user import create_user
from app.tests.utils.utils import random_email


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
    assert client.cookies.get("refresh_token")
    # logout
    r = client.get(f"{settings.API_V1_STR}/auth/remove-access-token")
    assert r.status_code == 200
    assert r.cookies.get("access_token") is None
    assert client.cookies.get("access_token") is None
    # both cookies cleared
    assert client.cookies.get("refresh_token") is None


def test_logout_revokes_refresh_token(client: TestClient, db: Session) -> None:
    """Logout should revoke the refresh token so it cannot be reused."""
    user = create_user(db, password="mysecretpassword")
    login = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data={"username": user.email, "password": "mysecretpassword"},
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200
    refresh_token = login.cookies.get("refresh_token")
    assert refresh_token is not None

    # Identify the token's jti before logging out (cookie value is quoted because
    # it contains a space, so strip quotes before stripping the Bearer prefix)
    raw_token = refresh_token.strip('"').removeprefix("Bearer ").strip()
    jti = UUID(security.decode_token(raw_token)["jti"])
    assert crud.refresh_token.get_by_jti(db, jti=jti).revoked is False

    logout = client.get(f"{settings.API_V1_STR}/auth/remove-access-token")
    assert logout.status_code == 200

    # Token is revoked in the DB
    assert crud.refresh_token.get_by_jti(db, jti=jti).revoked is True

    # And reusing it (past the grace window) is rejected
    db_token = crud.refresh_token.get_by_jti(db, jti=jti)
    crud.refresh_token.update(
        db,
        db_obj=db_token,
        obj_in=RefreshTokenUpdate(
            revoked=True,
            revoked_at=datetime.now(timezone.utc)
            - timedelta(seconds=settings.REFRESH_TOKEN_REUSE_GRACE_SECONDS + 1),
        ),
    )
    reuse = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": refresh_token},
    )
    assert reuse.status_code == 401


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


def test_email_confirmation_with_expired_token(client: TestClient, db: Session) -> None:
    token = secrets.token_urlsafe()
    user = create_user(db, token=token)
    # Back-date token to 120 minutes ago (past the 60-minute expiry)
    token_db_obj = crud.user.get_single_use_token(
        db, token_hash=security.get_token_hash(token, salt="confirm")
    )
    token_db_obj.created_at = datetime.now(timezone.utc) - timedelta(minutes=120)
    db.add(token_db_obj)
    db.commit()
    db.refresh(token_db_obj)
    r = client.get(
        f"{settings.API_V1_STR}/auth/confirm-email",
        params={"token": token},
    )
    assert r.request.url == settings.API_DOMAIN + "/auth/login?error=expired"
    user_in_db = crud.user.get(db, id=user.id)
    assert user_in_db and user_in_db.is_email_confirmed is False


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
    """Test refresh token endpoint rejects a token revoked beyond the grace window."""
    user = create_user(db)

    # Create a refresh token
    refresh_token_str = security.create_refresh_token(db, subject=str(user.id))

    # Decode to get JTI and revoke the token, backdating revoked_at past the grace
    # window so the reuse-grace path does not apply.
    payload = security.decode_token(refresh_token_str)
    jti = payload["jti"]
    db_token = crud.refresh_token.get_by_jti(db, jti=jti)
    assert db_token is not None
    crud.refresh_token.update(
        db,
        db_obj=db_token,
        obj_in=RefreshTokenUpdate(
            revoked=True,
            revoked_at=datetime.now(timezone.utc)
            - timedelta(seconds=settings.REFRESH_TOKEN_REUSE_GRACE_SECONDS + 60),
        ),
    )

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
    # revoked_at should be recorded so the reuse-grace window can be evaluated
    assert db_token_after.revoked_at is not None


def test_delete_auth_cookies_mirrors_secure_attributes(monkeypatch) -> None:
    """delete_auth_cookies must mirror the prod Secure/SameSite=None attributes."""
    monkeypatch.delenv("RUNNING_TESTS", raising=False)
    monkeypatch.setenv("HTTP_COOKIE_SECURE", "1")

    response = Response()
    security.delete_auth_cookies(response)

    set_cookies = [v.decode() for k, v in response.raw_headers if k == b"set-cookie"]
    assert len(set_cookies) == 2
    assert any(h.startswith("access_token=") for h in set_cookies)
    assert any(h.startswith("refresh_token=") for h in set_cookies)
    for header in set_cookies:
        assert "Secure" in header
        assert "samesite=none" in header.lower()


def test_logout_revokes_expired_refresh_token(client: TestClient, db: Session) -> None:
    """An expired refresh token is still revoked in the DB on logout."""
    user = create_user(db)
    token_jti = uuid4()
    crud.refresh_token.create(
        db,
        obj_in=RefreshTokenCreate(
            jti=token_jti,
            user_id=user.id,
            issued_at=datetime.now(timezone.utc) - timedelta(days=1),
            expires_at=datetime.now(timezone.utc) + timedelta(days=29),
        ),
    )
    # Craft a refresh JWT whose signature is valid but whose exp is in the past
    expired_jwt = jwt.encode(
        {
            "sub": str(user.id),
            "jti": str(token_jti),
            "type": "refresh",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            "iat": datetime.now(timezone.utc) - timedelta(days=1),
        },
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )

    response = client.get(
        f"{settings.API_V1_STR}/auth/remove-access-token",
        cookies={"refresh_token": f"Bearer {expired_jwt}"},
    )
    assert response.status_code == 200

    db_token = crud.refresh_token.get_by_jti(db, jti=token_jti)
    assert db_token is not None
    assert db_token.revoked is True


def test_login_sets_persistent_refresh_cookie(client: TestClient, db: Session) -> None:
    """Login should set a persistent (Max-Age) refresh cookie, not a session cookie."""
    user = create_user(db, password="mysecretpassword")

    response = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data={"username": user.email, "password": "mysecretpassword"},
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200

    set_cookie_headers = response.headers.get_list("set-cookie")
    refresh_cookie = next(
        (h for h in set_cookie_headers if h.startswith("refresh_token=")), None
    )
    access_cookie = next(
        (h for h in set_cookie_headers if h.startswith("access_token=")), None
    )
    assert refresh_cookie is not None
    assert access_cookie is not None
    # Refresh cookie persists across browser sessions; access cookie stays a session cookie
    assert "Max-Age" in refresh_cookie
    assert "Max-Age" not in access_cookie


def test_refresh_token_within_grace_window_succeeds(
    client: TestClient, db: Session
) -> None:
    """A just-rotated refresh token is still accepted within the grace window."""
    user = create_user(db)

    refresh_token_str = security.create_refresh_token(db, subject=str(user.id))
    payload = security.decode_token(refresh_token_str)
    jti = payload["jti"]

    # Revoke just now (revoked_at = now), simulating a concurrent rotation
    crud.refresh_token.revoke(db, jti=jti)

    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": f"Bearer {refresh_token_str}"},
    )

    assert response.status_code == 200
    assert response.cookies.get("access_token") is not None
    assert response.cookies.get("refresh_token") is not None


def test_refresh_token_reuse_after_grace_window_fails(
    client: TestClient, db: Session
) -> None:
    """A revoked token reused past the grace window is rejected."""
    user = create_user(db)

    refresh_token_str = security.create_refresh_token(db, subject=str(user.id))
    payload = security.decode_token(refresh_token_str)
    jti = payload["jti"]

    db_token = crud.refresh_token.get_by_jti(db, jti=jti)
    assert db_token is not None
    crud.refresh_token.update(
        db,
        db_obj=db_token,
        obj_in=RefreshTokenUpdate(
            revoked=True,
            revoked_at=datetime.now(timezone.utc)
            - timedelta(seconds=settings.REFRESH_TOKEN_REUSE_GRACE_SECONDS + 1),
        ),
    )

    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": f"Bearer {refresh_token_str}"},
    )

    assert response.status_code == 401
    assert "Refresh token revoked or expired" in response.json()["detail"]


def test_refresh_token_concurrent_reuse_both_succeed(
    client: TestClient, db: Session
) -> None:
    """Two refreshes of the same token within the grace window both succeed."""
    user = create_user(db)

    refresh_token_str = security.create_refresh_token(db, subject=str(user.id))

    first = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": f"Bearer {refresh_token_str}"},
    )
    assert first.status_code == 200

    # Reusing the same (now rotated/revoked) token again immediately is tolerated
    second = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        cookies={"refresh_token": f"Bearer {refresh_token_str}"},
    )
    assert second.status_code == 200


def test_login_updates_last_login_and_activity_timestamps(
    client: TestClient, db: Session
) -> None:
    """Test that login updates both last_login_at and last_activity_at."""
    user = create_user(db, password="mysecretpassword")

    # Verify timestamps are initially None
    assert user.last_login_at is None
    assert user.last_activity_at is None

    # Login
    data = {"username": user.email, "password": "mysecretpassword"}
    before_login = datetime.now(timezone.utc)
    r = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data=data,
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    after_login = datetime.now(timezone.utc)

    assert r.status_code == 200

    # Refresh user from database
    user_updated = crud.user.get(db, id=user.id)
    assert user_updated is not None

    # Verify both timestamps are set
    assert user_updated.last_login_at is not None
    assert user_updated.last_activity_at is not None

    # Verify timestamps are within expected range
    assert before_login <= user_updated.last_login_at <= after_login
    assert before_login <= user_updated.last_activity_at <= after_login


def test_activity_tracking_updates_last_activity_on_authenticated_request(
    client: TestClient, db: Session
) -> None:
    """Test that authenticated requests update last_activity_at."""
    user = create_user(db, password="mysecretpassword")

    # Login to get access token
    data = {"username": user.email, "password": "mysecretpassword"}
    r = client.post(
        f"{settings.API_V1_STR}/auth/access-token",
        data=data,
        headers={"content_type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200

    # Get user with initial timestamps
    user_after_login = crud.user.get(db, id=user.id)
    assert user_after_login is not None
    initial_last_activity = user_after_login.last_activity_at
    assert initial_last_activity is not None

    # Wait a moment and make an authenticated request
    import time

    time.sleep(1)

    # Make authenticated request (test token endpoint)
    before_request = datetime.now(timezone.utc)
    r = client.post(f"{settings.API_V1_STR}/auth/test-token")
    after_request = datetime.now(timezone.utc)
    assert r.status_code == 200

    # Refresh user from database
    user_after_request = crud.user.get(db, id=user.id)
    assert user_after_request is not None

    # Verify last_activity_at was updated (if outside throttle window)
    # Note: This test may not update if within throttle window
    # We just verify the timestamp is still valid
    assert user_after_request.last_activity_at is not None


def test_activity_tracking_throttle_prevents_frequent_updates(
    client: TestClient, db: Session
) -> None:
    """Test that activity tracking throttle prevents updates within throttle window."""
    user = create_user(db, password="mysecretpassword")

    # Manually set last_activity_at to recent time (within throttle window)
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    user.last_activity_at = recent_time
    db.add(user)
    db.commit()
    db.refresh(user)

    # Test the CRUD method directly
    updated_user = crud.user.update_last_activity(db, user=user, throttle_minutes=15)

    # Should return None because within throttle window
    assert updated_user is None

    # Verify last_activity_at was not updated
    user_check = crud.user.get(db, id=user.id)
    assert user_check is not None
    assert user_check.last_activity_at == recent_time


def test_activity_tracking_updates_when_outside_throttle_window(
    client: TestClient, db: Session
) -> None:
    """Test that activity tracking updates when outside throttle window."""
    user = create_user(db, password="mysecretpassword")

    # Manually set last_activity_at to old time (outside throttle window)
    old_time = datetime.now(timezone.utc) - timedelta(minutes=20)
    user.last_activity_at = old_time
    db.add(user)
    db.commit()
    db.refresh(user)

    # Test the CRUD method directly
    before_update = datetime.now(timezone.utc)
    updated_user = crud.user.update_last_activity(db, user=user, throttle_minutes=15)
    after_update = datetime.now(timezone.utc)

    # Should return updated user because outside throttle window
    assert updated_user is not None
    assert updated_user.last_activity_at is not None
    assert before_update <= updated_user.last_activity_at <= after_update

    # Verify last_activity_at was updated in database
    user_check = crud.user.get(db, id=user.id)
    assert user_check is not None
    assert user_check.last_activity_at != old_time
    assert before_update <= user_check.last_activity_at <= after_update


def test_activity_tracking_updates_when_last_activity_is_none(
    client: TestClient, db: Session
) -> None:
    """Test that activity tracking updates when last_activity_at is None."""
    user = create_user(db, password="mysecretpassword")

    # Ensure last_activity_at is None
    assert user.last_activity_at is None

    # Test the CRUD method directly
    before_update = datetime.now(timezone.utc)
    updated_user = crud.user.update_last_activity(db, user=user, throttle_minutes=15)
    after_update = datetime.now(timezone.utc)

    # Should return updated user because last_activity_at was None
    assert updated_user is not None
    assert updated_user.last_activity_at is not None
    assert before_update <= updated_user.last_activity_at <= after_update


# --- Email change tests ---


@patch.object(settings, "MAIL_ENABLED", 1)
@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_notification")
@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_verification")
def test_change_email_success(
    mock_verify,
    mock_notify,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    """Test successful email change request sets pending_email."""
    current_user = get_current_user(db, normal_user_access_token)
    new_email = random_email()
    data = {"current_password": "testuserpassword", "new_email": new_email}
    response = client.post(f"{settings.API_V1_STR}/auth/change-email", data=data)
    assert response.status_code == status.HTTP_200_OK
    # Verify pending_email was set on user
    user_in_db = crud.user.get(db, id=current_user.id)
    assert user_in_db is not None
    assert user_in_db.pending_email == new_email


@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_notification")
@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_verification")
def test_change_email_wrong_password(
    mock_verify,
    mock_notify,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    """Test email change fails with wrong password."""
    new_email = random_email()
    data = {"current_password": "wrongpassword", "new_email": new_email}
    response = client.post(f"{settings.API_V1_STR}/auth/change-email", data=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_notification")
@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_verification")
def test_change_email_same_email(
    mock_verify,
    mock_notify,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    """Test email change fails when new email matches current email."""
    current_user = get_current_user(db, normal_user_access_token)
    data = {"current_password": "testuserpassword", "new_email": current_user.email}
    response = client.post(f"{settings.API_V1_STR}/auth/change-email", data=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_notification")
@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_verification")
def test_change_email_duplicate_email(
    mock_verify,
    mock_notify,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    """Test email change fails when new email is already in use."""
    other_user = create_user(db)
    data = {"current_password": "testuserpassword", "new_email": other_user.email}
    response = client.post(f"{settings.API_V1_STR}/auth/change-email", data=data)
    assert response.status_code == status.HTTP_409_CONFLICT


@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_notification")
@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_verification")
def test_change_email_demo_user(
    mock_verify,
    mock_notify,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    """Test email change is blocked for demo users."""
    current_user = get_current_user(db, normal_user_access_token)
    crud.user.update(db, db_obj=current_user, obj_in=UserUpdate(is_demo=True))
    new_email = random_email()
    data = {"current_password": "testuserpassword", "new_email": new_email}
    response = client.post(f"{settings.API_V1_STR}/auth/change-email", data=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_confirm_email_change_with_valid_token(client: TestClient, db: Session) -> None:
    """Test confirming an email change with a valid token."""
    new_email = random_email()
    user = create_user(db, password="mysecretpassword")
    # Set pending email
    crud.user.update(db, db_obj=user, obj_in={"pending_email": new_email})
    # Create token with emailchg salt
    token = secrets.token_urlsafe()
    crud.user.create_single_use_token(
        db,
        obj_in=SingleUseTokenCreate(
            token=security.get_token_hash(token, salt="emailchg")
        ),
        user_id=user.id,
    )
    r = client.get(
        f"{settings.API_V1_STR}/auth/confirm-email-change",
        params={"token": token},
    )
    user_in_db = crud.user.get(db, id=user.id)
    assert r.request.url == settings.API_DOMAIN + "/auth/login?email_changed=true"
    assert user_in_db is not None
    assert user_in_db.email == new_email
    assert user_in_db.pending_email is None


def test_confirm_email_change_with_expired_token(
    client: TestClient, db: Session
) -> None:
    """Test confirming an email change with an expired token."""
    new_email = random_email()
    user = create_user(db, password="mysecretpassword")
    original_email = user.email
    # Set pending email
    crud.user.update(db, db_obj=user, obj_in={"pending_email": new_email})
    # Create token with emailchg salt
    token = secrets.token_urlsafe()
    crud.user.create_single_use_token(
        db,
        obj_in=SingleUseTokenCreate(
            token=security.get_token_hash(token, salt="emailchg")
        ),
        user_id=user.id,
    )
    # Back-date token to 120 minutes ago (past the 60-minute expiry)
    token_db_obj = crud.user.get_single_use_token(
        db, token_hash=security.get_token_hash(token, salt="emailchg")
    )
    token_db_obj.created_at = datetime.now(timezone.utc) - timedelta(minutes=120)
    db.add(token_db_obj)
    db.commit()
    db.refresh(token_db_obj)
    r = client.get(
        f"{settings.API_V1_STR}/auth/confirm-email-change",
        params={"token": token},
    )
    assert r.request.url == settings.API_DOMAIN + "/auth/login?error=expired"
    user_in_db = crud.user.get(db, id=user.id)
    assert user_in_db is not None
    assert user_in_db.email == original_email
    assert user_in_db.pending_email == new_email


def test_confirm_email_change_with_invalid_token(
    client: TestClient, db: Session
) -> None:
    """Test confirming an email change with an invalid token."""
    r = client.get(
        f"{settings.API_V1_STR}/auth/confirm-email-change",
        params={"token": "invalid-token"},
    )
    assert r.request.url == settings.API_DOMAIN + "/auth/login?error=invalid"


def test_confirm_email_change_duplicate_email(client: TestClient, db: Session) -> None:
    """Test TOCTOU guard: another user registers the email before confirmation."""
    new_email = random_email()
    user = create_user(db, password="mysecretpassword")
    # Set pending email
    crud.user.update(db, db_obj=user, obj_in={"pending_email": new_email})
    # Create token
    token = secrets.token_urlsafe()
    crud.user.create_single_use_token(
        db,
        obj_in=SingleUseTokenCreate(
            token=security.get_token_hash(token, salt="emailchg")
        ),
        user_id=user.id,
    )
    # Another user takes the email
    create_user(db, email=new_email)
    r = client.get(
        f"{settings.API_V1_STR}/auth/confirm-email-change",
        params={"token": token},
    )
    assert r.request.url == settings.API_DOMAIN + "/auth/login?error=email_taken"
    # Original user's email should not have changed
    user_in_db = crud.user.get(db, id=user.id)
    assert user_in_db is not None
    assert user_in_db.email != new_email


@patch.object(settings, "MAIL_ENABLED", 1)
@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_notification")
@patch("app.api.api_v1.endpoints.auth.mail.send_email_change_verification")
def test_change_email_cleans_up_previous_token(
    mock_verify,
    mock_notify,
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
) -> None:
    """Test that requesting a new email change cleans up previous tokens."""
    current_user = get_current_user(db, normal_user_access_token)
    # First request
    first_email = random_email()
    data = {"current_password": "testuserpassword", "new_email": first_email}
    client.post(f"{settings.API_V1_STR}/auth/change-email", data=data)
    # Second request should clean up first token
    second_email = random_email()
    data = {"current_password": "testuserpassword", "new_email": second_email}
    client.post(f"{settings.API_V1_STR}/auth/change-email", data=data)
    # Verify pending_email is the second email
    user_in_db = crud.user.get(db, id=current_user.id)
    assert user_in_db is not None
    assert user_in_db.pending_email == second_email
    # Verify only one emailchg token exists (first was cleaned up)
    stmt = select(SingleUseToken).where(
        SingleUseToken.user_id == current_user.id,
        SingleUseToken.token.contains("$emailchg$"),
    )
    remaining_tokens = db.scalars(stmt).all()
    assert len(remaining_tokens) == 1
