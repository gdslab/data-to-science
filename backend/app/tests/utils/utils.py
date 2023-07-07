from faker import Faker

from pydantic import PostgresDsn
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

from app.core.config import settings

faker = Faker()


def random_email() -> str:
    """Create random email address."""
    return faker.email()


def random_full_name() -> dict[str, str]:
    """Create random first and last name."""
    return {"first": faker.first_name(), "last": faker.last_name()}


def random_team_name() -> str:
    """Create random team name."""
    return faker.company()


def random_team_description() -> str:
    """Create random team description."""
    return faker.sentence()


def random_password() -> str:
    """Create random password."""
    return faker.password()


def build_sqlalchemy_uri(db_path: str) -> PostgresDsn:
    """Construct URI for test database."""
    return PostgresDsn.build(
        scheme="postgresql",
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        path=f"/{db_path}",
    )


def create_test_db(db_path: str) -> None:
    """Create test database if it does not already exist."""
    # connect to default "postgres" database
    engine = create_engine(build_sqlalchemy_uri(db_path="postgres"), pool_pre_ping=True)
    # attempt to create test database
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        try:
            connection.execute(text(f"CREATE DATABASE {db_path}"))
        except ProgrammingError:
            # duplicate database
            connection.rollback()
