import os

# These environment variables must be set before any `app` import so that the
# settings object and the security module pick them up at construction/import
# time (rather than at request time).
#
# Rate limiting is always disabled in tests. Unlike other feature flags, it is
# cross-cutting and causes unrelated tests to fail with 429s. Rate-limiting
# behaviour is verified via an isolated test app in test_rate_limiting.py.
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["RUNNING_TESTS"] = "1"

# Each pytest-xdist worker gets its own test database and its own on-disk static
# directory so parallel workers never share state. Falls back to "gw0" when
# running serially (PYTEST_XDIST_WORKER is unset).
worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
os.environ["TEST_STATIC_DIR"] = f"/tmp/static_{worker_id}"

import logging
import shutil
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from pystac_client import Client
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app import crud
from app.api.deps import get_db
from app.core.config import settings
from app.core.mail import fm
from app.db.base import Base
from app.main import app
from app.models.user import User
from app.seeds.seed_modules import seed_module_types
from app.tests.utils.user import (
    authentication_api_key_from_email,
    authentication_token_from_email,
)
from app.tests.utils.utils import build_sqlalchemy_uri, create_test_db
from app.utils.stac.STACCollectionManager import STACCollectionManager


logger = logging.getLogger(__name__)

TEST_DB_PATH = f"{settings.POSTGRES_DB or ''}_test_{worker_id}"
SQLALCHEMY_TEST_DATABASE_URI: PostgresDsn = build_sqlalchemy_uri(db_path=TEST_DB_PATH)

# Set True when this worker runs a STAC test; gates the shared-catalog cleanup.
_worker_ran_stac_tests = False


# Feature flag pytest markers for conditional test execution
pytest_requires_breedbase = pytest.mark.skipif(
    not settings.ENABLE_BREEDBASE,
    reason="Breedbase feature disabled (ENABLE_BREEDBASE=false)",
)

pytest_requires_campaigns = pytest.mark.skipif(
    not settings.ENABLE_CAMPAIGNS,
    reason="Campaigns feature disabled (ENABLE_CAMPAIGNS=false)",
)

pytest_requires_mail = pytest.mark.skipif(
    not settings.MAIL_ENABLED,
    reason="Mail feature disabled (MAIL_ENABLED=false)",
)

pytest_requires_iforester = pytest.mark.skipif(
    not settings.ENABLE_IFORESTER,
    reason="iForester feature disabled (ENABLE_IFORESTER=false)",
)

pytest_requires_stac = pytest.mark.skipif(
    not settings.ENABLE_STAC, reason="STAC feature disabled (ENABLE_STAC=false)"
)


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """Create the test database schema once per worker.

    The schema is built a single time per test session (per xdist worker).
    Between tests the tables are truncated rather than dropped and recreated --
    eliminating the per-test DDL that previously dominated the suite's runtime --
    so each test still runs against an empty, freshly seeded database.
    """
    create_test_db(db_path=TEST_DB_PATH)
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URI.unicode_string(), pool_pre_ping=True
    )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def reset_database(session: Session) -> None:
    """Return the database to a clean, seeded state for a single test.

    Truncating with ``CASCADE`` clears every application table in one statement
    (PostGIS's ``spatial_ref_sys`` and other non-model tables are left intact),
    then reference data is re-seeded. Each ``create``/``update`` the test
    performs commits in its own transaction, preserving the per-operation
    timestamp semantics that some tests rely on.
    """
    table_names = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    session.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))
    session.commit()
    seed_module_types(session=session)


@pytest.fixture(name="db")
def db_fixture(db_engine: Engine) -> Generator[Session, None, None]:
    """Provide a clean, seeded database session for each test."""
    SessionLocal = sessionmaker(
        autoflush=False, expire_on_commit=False, bind=db_engine
    )
    session = SessionLocal()
    reset_database(session)
    try:
        yield session
    finally:
        session.close()
        # Files written to disk by helpers/endpoints are not transactional and
        # must be removed between tests.
        if os.path.exists(settings.TEST_STATIC_DIR):
            shutil.rmtree(settings.TEST_STATIC_DIR)


@pytest.fixture(name="client")
def client_fixture(db: Session) -> Generator[TestClient, None, None]:
    """Generate an API test client backed by the per-test database session."""

    def get_db_override() -> Session:
        return db

    app.dependency_overrides[get_db] = get_db_override

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(name="normal_user_access_token")
def normal_user_access_token(client: TestClient, db: Session) -> str:
    """Authenticate the test client as the normal user and return its access token."""
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


@pytest.fixture(name="normal_user_api_key")
def normal_user_api_key(client: TestClient, db: Session) -> str:
    """Authenticate the test client as the normal user and return its API key."""
    return authentication_api_key_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


@pytest.fixture(name="current_user")
def current_user_fixture(client: TestClient, db: Session) -> User:
    """Authenticate the test client as the normal user and return the User object.

    Logging in sets the access-token cookie on ``client`` (so subsequent requests
    made with that client are authenticated) and this returns the matching
    ``User`` row, replacing the ``get_current_user(db, token)`` boilerplate
    previously repeated across API tests.
    """
    authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
    user = crud.user.get_by_email(db, email=settings.EMAIL_TEST_USER)
    assert user is not None
    return user


@pytest.fixture(autouse=True)
def suppress_outbound_email() -> None:
    """Suppress real email delivery for every test.

    Tests that assert on email content capture it with ``fm.record_messages()``;
    other endpoints (e.g. user creation) trigger a confirmation email as a
    background task. Without deterministic suppression, those background sends
    hit a real SMTP server and fail for the reserved ``example.*`` domains that
    faker generates -- a failure that previously only stayed hidden because an
    earlier test in the same process happened to set ``SUPPRESS_SEND`` first.
    """
    if fm:
        fm.config.SUPPRESS_SEND = 1


@pytest.fixture(scope="session", autouse=True)
def cleanup_stac_catalog() -> Generator[None, None, None]:
    """Clean up any leaked collections from the shared test STAC catalog.

    STAC tests run against a single shared external catalog, so they are confined
    to one xdist worker (see ``pytest_collection_modifyitems``). Only that worker
    performs the catalog-wide cleanup, and only after all of its tests have
    finished, so it never deletes collections another worker is still using.
    """
    yield  # Let all tests run first

    if not _worker_ran_stac_tests:
        return

    try:
        # Connect to STAC API
        stac_url = settings.get_stac_api_url
        if not stac_url:
            return

        client = Client.open(str(stac_url))
        collections = client.get_collections()

        # Remove all collections since this is a test-only catalog
        for collection in collections:
            collection_id = collection.id
            if collection_id:
                try:
                    logger.info(f"Cleaning up collection {collection_id}")
                    scm = STACCollectionManager(collection_id=collection_id)
                    scm.remove_from_catalog()
                except Exception as e:
                    logger.error(
                        f"Failed to cleanup collection {collection_id}: {str(e)}"
                    )
    except Exception as e:
        logger.error(f"Failed to cleanup STAC catalog: {str(e)}")


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Confine STAC tests to a single xdist worker.

    They share one external STAC catalog, so running them concurrently across
    workers causes collisions. Assigning them all to the same ``xdist_group``
    makes ``--dist loadgroup`` schedule them onto one worker, where they run
    serially relative to each other.

    ``tryfirst`` is required: this conftest loads as an *initial* conftest
    (``testpaths`` in pytest.ini, pytest >= 8.1), i.e. before xdist's worker
    plugin registers. Hooks run last-registered-first, so without ``tryfirst``
    xdist's own ``pytest_collection_modifyitems`` -- which turns ``xdist_group``
    markers into the ``@group`` nodeid suffix the loadgroup scheduler groups
    by -- would run before this hook and see no markers, silently scattering
    STAC tests across all workers.
    """
    for item in items:
        if "stac" in item.nodeid.lower():
            item.add_marker(pytest.mark.xdist_group("stac"))


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Record when the current worker runs a STAC test (see cleanup_stac_catalog)."""
    if "stac" in item.nodeid.lower():
        global _worker_ran_stac_tests
        _worker_ran_stac_tests = True
