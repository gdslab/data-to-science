import secrets
from typing import Any

from pydantic import (
    EmailStr,
    field_validator,
    FieldValidationInfo,
    PostgresDsn,
)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "dev"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    PROJECT_NAME: str = ""
    UPLOAD_DIR: str = "/user-data"
    TEST_UPLOAD_DIR: str = "/tmp/testing"
    STATIC_URL: str = "http://localhost/static"

    POSTGRES_HOST: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: str | None, info: FieldValidationInfo) -> Any:
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

    EMAIL_TEST_USER: EmailStr = "test@example.com"  # type: ignore

    LOGGER_FILE: str = ""


settings = Settings()
