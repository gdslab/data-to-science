import secrets
from typing import Any

from fastapi_mail.config import ConnectionConfig
from pydantic import EmailStr, field_validator, ValidationInfo, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "dev"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = ""
    # Secret key used for signing pg_tileserv and titiler requests
    TILE_SIGNING_SECRET_KEY: str = ""

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

    # Provide mapbox token for worldwide satellite imagery (optional)
    MAPBOX_ACCESS_TOKEN: str | None = None

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
    MAIL_PASSWORD: str = ""
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


settings = Settings()
