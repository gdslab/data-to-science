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

import httpx
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

from app.core.config import settings
from app.models.single_use_token import SingleUseToken

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
    from app import crud
    from app.schemas.refresh_token import RefreshTokenCreate

    refresh_token_create = RefreshTokenCreate(
        jti=jti, user_id=user_uuid, issued_at=now, expires_at=expire
    )
    crud.refresh_token.create(db, obj_in=refresh_token_create)

    return token


def decode_token(token: str, verify_exp: bool = True) -> dict[str, Any]:
    """Decode JWT token and return payload.

    The signature is always verified. ``verify_exp=False`` skips only the
    expiration check, which logout uses so an expired refresh token's ``jti`` can
    still be extracted and revoked in the database.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"verify_exp": verify_exp},
    )


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
    return datetime.now(tz=timezone.utc) > (
        token.created_at + timedelta(minutes=minutes)
    )


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


def _resolve_cookie_security() -> tuple[bool, Literal["lax", "strict", "none"]]:
    """Resolve the secure/samesite cookie attributes from the environment.

    Production (HTTPS) issues ``Secure``, ``SameSite=None`` cookies so they work
    cross-origin. Tests and non-HTTPS/quickstart deployments fall back to
    ``secure=False``, ``samesite="lax"``. Both setting and deleting auth cookies
    must use these same attributes, otherwise browsers may refuse to apply the
    deletion in a cross-site context and the cookie lingers.
    """
    # Import here to avoid circular imports
    from app.api.utils import str_to_bool

    secure_cookie = True
    samesite: Literal["lax", "strict", "none"] = "none"
    try:
        if str_to_bool(os.environ.get("RUNNING_TESTS", False)) or not str_to_bool(
            os.environ.get("HTTP_COOKIE_SECURE", True)
        ):
            secure_cookie = False
            samesite = "lax"
    except ValueError:
        logger.exception("Defaulting to secure cookie")

    return secure_cookie, samesite


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set authentication cookies with proper security settings.

    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token
    """
    secure_cookie, samesite = _resolve_cookie_security()

    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=secure_cookie,
        samesite=samesite,
    )
    # Set refresh token cookie. Unlike the access token, give the refresh cookie an
    # explicit max_age so it persists across browser sessions for the full refresh
    # token lifetime; otherwise it becomes a session cookie and is dropped when the
    # browser session ends, forcing the user to log in again on their next visit.
    response.set_cookie(
        key="refresh_token",
        value=f"Bearer {refresh_token}",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=secure_cookie,
        samesite=samesite,
    )


def delete_auth_cookies(response: Response) -> None:
    """Clear the auth cookies, mirroring the attributes used to set them.

    The deletion ``Set-Cookie`` must carry the same ``secure``/``samesite``
    attributes as ``set_auth_cookies``; otherwise a browser may reject clearing a
    ``SameSite=None; Secure`` cookie from a cross-site context, leaving the user
    effectively logged in.
    """
    secure_cookie, samesite = _resolve_cookie_security()
    for key in ("access_token", "refresh_token"):
        response.delete_cookie(
            key=key,
            path="/",
            httponly=True,
            secure=secure_cookie,
            samesite=samesite,
        )


async def validate_turnstile(
    token: str, secret: str, remoteip: str | None = None
) -> dict[str, Any]:
    """Validate Cloudflare Turnstile token.

    Args:
        token: Turnstile response token from the client
        secret: Turnstile secret key
        remoteip: Optional client IP address for additional validation

    Returns:
        dict: Validation response from Cloudflare containing 'success' boolean
              and potentially 'error-codes' if validation fails

    Example response:
        {
            "success": true,
            "challenge_ts": "2023-01-01T12:00:00Z",
            "hostname": "example.com"
        }
    """
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    data = {"secret": secret, "response": token}

    if remoteip:
        data["remoteip"] = remoteip

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Turnstile validation error: {e}")
        return {"success": False, "error-codes": ["internal-error"]}
    except Exception as e:
        logger.error(f"Unexpected error during Turnstile validation: {e}")
        return {"success": False, "error-codes": ["internal-error"]}


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
