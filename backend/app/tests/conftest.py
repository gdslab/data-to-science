import os
import shutil
from typing import Generator

import pytest
from pytest import Config
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.tests.utils.utils import build_sqlalchemy_uri, create_test_db
from app.tests.utils.user import (
    authentication_api_key_from_email,
    authentication_token_from_email,
)
from app.seeds.seed_modules import seed_module_types


TEST_DB_PATH = f"{settings.POSTGRES_DB or ''}_test"
SQLALCHEMY_TEST_DATABASE_URI: PostgresDsn = build_sqlalchemy_uri(db_path=TEST_DB_PATH)


os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(name="db")
def db_fixture() -> Generator:
    """Generate database session for each test."""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URI.unicode_string(), pool_pre_ping=True
    )
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autoflush=False, bind=engine)
    try:
        db = TestSessionLocal()
        # Seed module types
        seed_module_types(session=db)
        yield db
    except Exception as exception:
        db.rollback()
        exception_name = exception.__class__.__name__
        if exception_name == "JWTError" or exception_name == "JWSSignatureError":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Must sign in to access",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to complete request",
            )
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        if os.path.exists(settings.TEST_STATIC_DIR):
            shutil.rmtree(settings.TEST_STATIC_DIR)


@pytest.fixture(name="client")
def client_fixture(db: Session) -> Generator:
    """Generate client for each api test."""

    def get_db_override() -> Session:
        return db

    app.dependency_overrides[get_db] = get_db_override

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(name="normal_user_access_token")
def normal_user_access_token(client: TestClient, db: Session) -> str:
    """Retrieve access token header for normal (non-superuser) user."""
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


@pytest.fixture(name="normal_user_api_key")
def normal_user_api_key(client: TestClient, db: Session) -> str:
    """Retrieve api key header for normal (non-superuser) user."""
    return authentication_api_key_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


def pytest_configure(config: Config) -> None:
    """Create the test database before running tests if necessary."""
    create_test_db(db_path=TEST_DB_PATH)
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URI.unicode_string(), pool_pre_ping=True
    )
    # drop any existing tables in test dataase
    Base.metadata.drop_all(engine)
    # create tables
    Base.metadata.create_all(engine)
    # seed module types
    TestSessionLocal = sessionmaker(autoflush=False, bind=engine)
    session = TestSessionLocal()
    try:
        seed_module_types(session=session)
    finally:
        session.close()
