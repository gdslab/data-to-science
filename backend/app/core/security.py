from datetime import datetime, timedelta
from typing import Any, cast, Dict, Optional

from fastapi import Request, status
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt
from passlib.context import CryptContext
from passlib.hash import sha256_crypt

from app.core.config import settings
from app.models.confirmation_token import ConfirmationToken


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


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare plain text password against hashed password and return true if match."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Use bcrypt to create hashed password."""
    return pwd_context.hash(password)


def get_token_hash(token: str, salt: str) -> str:
    """Create SHA256 hash of token."""
    return sha256_crypt.using(salt=salt).hash(token)


def check_token_expired(token: ConfirmationToken) -> bool:
    """Check if token is older than one hour."""
    return datetime.now() > (token.created_at + timedelta(minutes=60))


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
