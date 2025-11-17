import os
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


class Settings(BaseSettings):
    ENV: str = "dev"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = ""
    # Secret key used for signing pg_tileserv and titiler requests
    TILE_SIGNING_SECRET_KEY: str = ""

    @field_validator("SECRET_KEY", "TILE_SIGNING_SECRET_KEY", mode="before")
    def validate_secret_keys(cls, v: str | None, info: ValidationInfo) -> str:
        field_name = info.field_name
        if not v or v.strip() == "":
            raise ValueError(
                f"{field_name} environment variable must be set and cannot be empty"
            )
        if len(v) < 32:
            raise ValueError(f"{field_name} must be at least 32 characters long")
        return v

    # 15 minutes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    # Activity tracking throttle in minutes (only update last_activity_at if older than this)
    ACTIVITY_TRACKING_THROTTLE_MINUTES: int = 15

    API_PROJECT_NAME: str = ""
    API_DOMAIN: str = ""
    TEST_STATIC_DIR: str = "/tmp/static"
    STATIC_DIR: str = "/static"
    POTREE_DIR: str = "/app/potree"
    PC_GLTF_VIEWER_DIR: str = "/app/pc-gltf-viewer"

    API_LOGDIR: str = "/app/logs"

    # OpenTelemetry
    ENABLE_OPENTELEMETRY: bool = False

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

    # Feature flags for optional modules
    ENABLE_BREEDBASE: bool = False
    ENABLE_CAMPAIGNS: bool = False
    ENABLE_IFORESTER: bool = False
    ENABLE_STAC: bool = False

    # STAC Catalog
    STAC_API_URL: Optional[AnyHttpUrl] = None
    STAC_API_TEST_URL: Optional[AnyHttpUrl] = None
    STAC_BROWSER_URL: Optional[AnyHttpUrl] = None
    EXTERNAL_VIEWER_URL: Optional[AnyHttpUrl] = None

    @field_validator(
        "EXTERNAL_VIEWER_URL",
        "STAC_API_URL",
        "STAC_API_TEST_URL",
        "STAC_BROWSER_URL",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

    @property
    def get_stac_api_url(self) -> Optional[AnyHttpUrl]:
        """Get the appropriate STAC API URL based on whether we're running tests."""
        # Check if we're running tests
        if os.getenv("RUNNING_TESTS") == "1" and self.STAC_API_TEST_URL:
            return self.STAC_API_TEST_URL
        return self.STAC_API_URL


settings = Settings()
