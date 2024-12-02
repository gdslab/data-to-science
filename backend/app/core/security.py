import base64
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, cast, Dict, Optional
from urllib.parse import urlencode, quote_plus

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
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_signed_url(
    base_url: str,
    filter_param: str,
    limit_param: int = 50000,
    expiration_seconds: int = 3600,
) -> str:
    """Generate a signed URL for fetching raster and vector tiles.

    Args:
        base_url (str): Base URL for fetching tile.
        filter_param (str): Filter query parameter to be included with request.
        limit_param (str): Max number of features to write to a tile.
        expiration_seconds (int, optional): Expiration in seconds. Defaults to 3600.

    Returns:
        str: Signed URL.
    """
    # Set expiration for N (default 3600) seconds from now
    expiration_timestamp = int(time.time()) + expiration_seconds

    # Include `filter` and `limit` query params in the hash
    encoded_filter = quote_plus(filter_param)
    encoded_limit = quote_plus(str(limit_param))
    string_to_hash = f"{expiration_timestamp}{encoded_filter}{encoded_limit} {settings.TILE_SIGNING_SECRET_KEY}"

    hash_binary = hashlib.md5(string_to_hash.encode()).digest()
    secure_hash = base64.urlsafe_b64encode(hash_binary).decode().rstrip("=")

    # Build the query param string
    query_params = {
        "expires": expiration_timestamp,
        "filter": filter_param,
        "limit": limit_param,
        "secure": secure_hash,
    }

    return f"{base_url}?{urlencode(query_params)}"


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
    return datetime.now() > (token.created_at + timedelta(minutes))


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
