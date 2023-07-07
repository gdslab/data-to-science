from typing import Generator

import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.tests.utils.utils import build_sqlalchemy_uri, create_test_db
from app.tests.utils.user import authentication_token_from_email


TEST_DB_PATH = f"{settings.POSTGRES_DB or ''}_test"
SQLALCHEMY_TEST_DATABASE_URI: PostgresDsn = build_sqlalchemy_uri(db_path=TEST_DB_PATH)


@pytest.fixture(name="db")
def db_fixture() -> Generator:
    """Generate database session for each test."""
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URI, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autoflush=False, bind=engine)
    try:
        db = TestSessionLocal()
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        Base.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(db: Session) -> Generator:
    """Generate client for each api test."""

    def get_db_override():
        return db

    app.dependency_overrides[get_db] = get_db_override

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(name="normal_user_token_headers")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Retrieve access token header for normal (non-superuser) user."""
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


def pytest_configure(config):
    """Create the test database before running tests if necessary."""
    create_test_db(db_path=TEST_DB_PATH)
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URI, pool_pre_ping=True  # type: ignore
    )
    # drop any existing tables in test dataase
    Base.metadata.drop_all(engine)
