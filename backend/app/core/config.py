import os
import secrets
from typing import Any, Optional

from fastapi_mail.config import ConnectionConfig
from pydantic import (
    AnyHttpUrl,
    EmailStr,
    field_validator,
    ValidationInfo,
    PostgresDsn,
    SecretStr,
)
from pydantic_settings import BaseSettings

from app.core.utils import generate_secret_key


class Settings(BaseSettings):
    ENV: str = "dev"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = generate_secret_key()
    # Secret key used for signing pg_tileserv and titiler requests
    TILE_SIGNING_SECRET_KEY: str = generate_secret_key()

    @field_validator("SECRET_KEY", mode="before")
    def generate_secret_key(cls, v: str | None) -> str:
        if not v:
            return secrets.token_urlsafe(32)
        return v

    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    API_PROJECT_NAME: str = ""
    API_DOMAIN: str = ""
    TEST_STATIC_DIR: str = "/tmp/static"
    STATIC_DIR: str = "/static"
    POTREE_DIR: str = "/app/potree"

    API_LOGDIR: str = "/app/logs"

    # Provide a base URL for shortened URLs (e.g., "http://localhost:8000/s")
    SHORTENED_URL_BASE: str = API_DOMAIN + "/sl"

    @field_validator("SHORTENED_URL_BASE", mode="before")
    def validate_shortened_url_base(cls, v: str | None, info: ValidationInfo) -> str:
        values = info.data
        api_domain = values.get("API_DOMAIN")
        if not api_domain:
            raise ValueError("API_DOMAIN must be set to validate SHORTENED_URL_BASE")

        return api_domain + v

    # Provide mapbox token for worldwide satellite imagery (optional)
    MAPBOX_ACCESS_TOKEN: str | None = None

    # Point limit for point cloud preview generation
    POINT_LIMIT: int = 1_000_000

    # Database
    POSTGRES_HOST: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        return PostgresDsn.build(
            scheme="postgresql",
            host=values.get("POSTGRES_HOST"),
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            path=values.get("POSTGRES_DB"),
        )

    # Email
    MAIL_ENABLED: int = 0
    MAIL_ADMINS: str = ""
    MAIL_USERNAME: EmailStr | str = ""
    MAIL_PASSWORD: SecretStr = SecretStr("")
    MAIL_FROM: EmailStr | str = ""
    MAIL_FROM_NAME: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = ""
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    MAIL_CONF: ConnectionConfig | None = None

    @field_validator("MAIL_CONF", mode="before")
    def assemble_mail_conf(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        if values.get("MAIL_ENABLED"):
            return ConnectionConfig.model_construct(
                MAIL_USERNAME=values.get("MAIL_USERNAME"),
                MAIL_PASSWORD=values.get("MAIL_PASSWORD"),
                MAIL_FROM=values.get("MAIL_FROM"),
                MAIL_FROM_NAME=values.get("MAIL_FROM_NAME"),
                MAIL_PORT=values.get("MAIL_PORT"),
                MAIL_SERVER=values.get("MAIL_SERVER"),
                MAIL_STARTTLS=values.get("MAIL_STARTTLS"),
                MAIL_SSL_TLS=values.get("MAIL_SSL_TLS"),
                USE_CREDENTIALS=values.get("USE_CREDENTIALS"),
                VALIDATE_CERTS=values.get("VALIDATE_CERTS"),
            )
        else:
            return None

    # Testing
    EMAIL_TEST_USER: EmailStr = "test@example.com"  # type: ignore

    # STAC Catalog
    STAC_API_URL: Optional[AnyHttpUrl] = None
    STAC_API_TEST_URL: Optional[AnyHttpUrl] = None
    STAC_BROWSER_URL: Optional[AnyHttpUrl] = None

    @property
    def get_stac_api_url(self) -> Optional[AnyHttpUrl]:
        """Get the appropriate STAC API URL based on whether we're running tests."""
        # Check if we're running tests
        if os.getenv("RUNNING_TESTS") == "1" and self.STAC_API_TEST_URL:
            return self.STAC_API_TEST_URL
        return self.STAC_API_URL


settings = Settings()
