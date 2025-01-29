import base64
import hmac
import hashlib
import time
from datetime import datetime, timedelta, timezone
from typing import Any, cast, Dict, Optional, Tuple

from fastapi import Request, status
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt
from passlib.context import CryptContext
from passlib.hash import sha256_crypt

from app.core.config import settings
from app.models.single_use_token import SingleUseToken


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
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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
