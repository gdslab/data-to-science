from datetime import datetime, timedelta, timezone
import uuid

import pytest
from jose import jwt
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.core.security import create_refresh_token, decode_token, ALGORITHM
from app.tests.utils.user import create_user


def test_create_refresh_token_creates_jwt_and_db_entry(db: Session) -> None:
    """Test that create_refresh_token creates both JWT and database entry."""
    user = create_user(db)

    # Create refresh token
    token_str = create_refresh_token(db, subject=str(user.id))

    # Verify JWT token is created
    assert token_str
    assert isinstance(token_str, str)
    assert len(token_str.split(".")) == 3  # JWT has 3 parts

    # Decode and verify JWT payload
    payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == str(user.id)
    assert payload["type"] == "refresh"
    assert "jti" in payload
    assert "iat" in payload
    assert "exp" in payload

    # Verify database entry is created
    jti = uuid.UUID(payload["jti"])
    db_token = crud.refresh_token.get_by_jti(db, jti=jti)
    assert db_token
    assert db_token.user_id == user.id
    assert not db_token.revoked


def test_create_refresh_token_with_custom_expiration(db: Session) -> None:
    """Test creating refresh token with custom expiration time."""
    user = create_user(db)
    custom_expire = datetime.now(timezone.utc) + timedelta(hours=1)

    token_str = create_refresh_token(db, subject=str(user.id), expire=custom_expire)

    # Decode and verify expiration
    payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[ALGORITHM])
    token_exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    # Allow for small time differences due to processing
    assert abs((token_exp - custom_expire).total_seconds()) < 2


def test_create_refresh_token_default_expiration(db: Session) -> None:
    """Test that default expiration is set correctly."""
    user = create_user(db)

    token_str = create_refresh_token(db, subject=str(user.id))

    payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[ALGORITHM])
    token_exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    token_iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

    # Verify expiration is approximately REFRESH_TOKEN_EXPIRE_DAYS from issued time
    expected_duration = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    actual_duration = token_exp - token_iat

    # Allow for small time differences
    assert abs((actual_duration - expected_duration).total_seconds()) < 2


def test_create_refresh_token_unique_jti(db: Session) -> None:
    """Test that each refresh token gets a unique JTI."""
    user = create_user(db)

    token1_str = create_refresh_token(db, subject=str(user.id))
    token2_str = create_refresh_token(db, subject=str(user.id))

    payload1 = jwt.decode(token1_str, settings.SECRET_KEY, algorithms=[ALGORITHM])
    payload2 = jwt.decode(token2_str, settings.SECRET_KEY, algorithms=[ALGORITHM])

    assert payload1["jti"] != payload2["jti"]


def test_decode_token_works_with_refresh_token(db: Session) -> None:
    """Test that decode_token function works with refresh tokens."""
    user = create_user(db)

    token_str = create_refresh_token(db, subject=str(user.id))

    # Use the decode_token function
    payload = decode_token(token_str)

    assert payload["sub"] == str(user.id)
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_create_refresh_token_with_invalid_subject(db: Session) -> None:
    """Test creating refresh token with invalid subject raises appropriate error."""
    # This should raise a ValueError when trying to convert to UUID
    with pytest.raises(ValueError):
        create_refresh_token(db, subject="not-a-valid-uuid")


def test_refresh_token_payload_structure(db: Session) -> None:
    """Test that refresh token payload has all required fields."""
    user = create_user(db)

    token_str = create_refresh_token(db, subject=str(user.id))
    payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[ALGORITHM])

    # Verify all required fields are present
    required_fields = ["sub", "jti", "iat", "exp", "type"]
    for field in required_fields:
        assert field in payload

    # Verify field types and values
    assert isinstance(payload["sub"], str)
    assert isinstance(payload["jti"], str)
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["exp"], int)
    assert payload["type"] == "refresh"

    # Verify JTI is a valid UUID string
    uuid.UUID(payload["jti"])  # This will raise ValueError if invalid
