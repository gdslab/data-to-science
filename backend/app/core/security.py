import base64
import hmac
import hashlib
import time
import os
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, cast, Dict, Optional, Tuple, Literal
from uuid import UUID

from fastapi import Request, Response, status, HTTPException
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
from passlib.hash import sha256_crypt
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.single_use_token import SingleUseToken
from app.schemas.refresh_token import RefreshTokenCreate

logger = logging.getLogger("__name__")

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",  # only allow bcrypt
)

ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expire: datetime | None = None) -> str:
    """Create JWT access token with expiration defined in settings."""
    if not expire:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    db: Session, subject: str | Any, expire: datetime | None = None
) -> str:
    """Create JWT refresh token with expiration defined in settings."""
    # Create a unique identifier for the token
    jti = uuid.uuid4()

    # Set expiration date
    now = datetime.now(timezone.utc)
    if not expire:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Create payload
    to_encode = {
        "sub": str(subject),
        "jti": str(jti),
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }

    # Encode token
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    # Handle subject being either string or UUID
    if isinstance(subject, UUID):
        user_uuid = subject
    else:
        user_uuid = UUID(subject)

    # Store token in database
    refresh_token_create = RefreshTokenCreate(
        jti=jti, user_id=user_uuid, issued_at=now, expires_at=expire
    )
    crud.refresh_token.create(db, obj_in=refresh_token_create)

    return token


def decode_token(token: str) -> dict[str, Any]:
    """Decode JWT token and return payload."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def sign_map_tile_payload(payload: str, expiration: int = 600) -> Tuple[str, int]:
    """Returns signed payload for either raster or vector tile data.

    Args:
        payload (str): Payload to be signed.
        expiration (int, optional): Expiration duration. Defaults to 600.
    Returns:
        Tuple[str, int]: Signed payload and expiration timestamp.
    """
    # Add expiration duration to current time
    expiration_timestamp = int(time.time()) + expiration

    # Append expiration timestamp to front of payload
    payload_with_timestamp = str(expiration_timestamp) + payload

    # Create SHA256 hash
    payload_signed = hmac.new(
        base64.b64decode(settings.TILE_SIGNING_SECRET_KEY),
        payload_with_timestamp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"0x{payload_signed}", expiration_timestamp


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare plain text password against hashed password and return true if match."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Use bcrypt to create hashed password."""
    return pwd_context.hash(password)


def get_token_hash(token: str, salt: str) -> str:
    """Create SHA256 hash of token."""
    return sha256_crypt.using(salt=salt).hash(token)


def check_token_expired(token: SingleUseToken, minutes: int = 60) -> bool:
    """Check if token is older than value passed in minutes (defaults to 1 hour)."""
    return datetime.now(tz=timezone.utc) > (token.created_at + timedelta(minutes))


def validate_token_and_get_payload(token: str, expected_type: str) -> dict[str, Any]:
    """Validate JWT token, check type, and return payload with proper error handling.

    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        dict: Token payload

    Raises:
        HTTPException: For various token validation failures
    """
    # Decode token and handle expiration specifically
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        token_type_title = expected_type.title()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{token_type_title} token expired",
        )
    except Exception:
        token_type_title = expected_type.title()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid {expected_type} token",
        )

    # Check if token is the expected type
    if payload.get("type") != expected_type:
        token_type_title = expected_type.title()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid {expected_type} token",
        )

    return payload


def get_user_from_token_payload(db: Session, payload: dict[str, Any]):
    """Get user from JWT token payload with proper validation.

    Args:
        db: Database session
        payload: JWT token payload

    Returns:
        User model instance

    Raises:
        HTTPException: For various user lookup failures
    """
    # Get user id from payload and confirm it is a valid UUID
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user id"
        )

    try:
        user_uuid = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user id"
        )

    # Import here to avoid circular imports
    from app import crud

    # Get user from database
    user = crud.user.get_by_id(db, user_id=user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set authentication cookies with proper security settings.

    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token
    """
    # Import here to avoid circular imports
    from app.api.utils import str_to_bool

    # Toggle secure off if running tests
    secure_cookie = True
    samesite: Literal["lax", "strict", "none"] | None = "none"
    try:
        if str_to_bool(os.environ.get("RUNNING_TESTS", False)) or not str_to_bool(
            os.environ.get("HTTP_COOKIE_SECURE", True)
        ):
            secure_cookie = False
            samesite = "lax"
    except ValueError:
        logger.exception("Defaulting to secure cookie")

    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=secure_cookie,
        samesite=samesite,
    )
    # Set refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=f"Bearer {refresh_token}",
        httponly=True,
        secure=secure_cookie,
        samesite=samesite,
    )


class OAuth2PasswordBearerWithCookie(OAuth2):
    """
    Modified OAuth2PasswordBearer class that uses cookies instead of
    Authorization header. Replaced line is commented out - otherwise identical
    to original OAuth2PasswordBearer class.
    """

    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            password=cast(Any, {"tokenUrl": tokenUrl, "scopes": scopes})
        )
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Optional[str]:
        # authorization = request.headers.get("Authorization")
        authorization = request.cookies.get("access_token")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param
