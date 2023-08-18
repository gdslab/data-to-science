import secrets
from typing import Any

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, PostgresDsn, validator


class Settings(BaseSettings):
    ENV: str = "dev"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    PROJECT_NAME: str = ""
    UPLOAD_DIR: str = "/user-data"
    TEST_UPLOAD_DIR: str = "/tmp/testing"
    STATIC_URL: AnyHttpUrl = "http://localhost/static"

    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "ps2"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "ps2"
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: str | None, values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    EMAIL_TEST_USER: EmailStr = "test@example.com"  # type: ignore

    LOGGER_FILE: str = ""

    class Config:
        case_sensitive = True


settings = Settings()
