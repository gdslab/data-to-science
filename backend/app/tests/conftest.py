from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.tests.utils.user import authentication_token_from_email


@pytest.fixture(scope="session")
def db() -> Generator:
    """Generate database session for each test."""
    yield SessionLocal()


@pytest.fixture(scope="module")
def client() -> Generator:
    """Generate TestClient for each test."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Retrieve access token header for normal (non-superuser) user."""
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
