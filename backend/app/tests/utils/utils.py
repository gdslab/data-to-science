from faker import Faker

from geojson_pydantic import FeatureCollection
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
    return faker.password(length=12)


def build_sqlalchemy_uri(db_path: str) -> PostgresDsn:
    """Construct URI for test database."""
    return PostgresDsn.build(
        scheme="postgresql",
        host=settings.POSTGRES_HOST,
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        path=db_path,
    )


def create_test_db_postgis_extension(db_path: str) -> None:
    """Add postgis extension to test database."""
    # connect to test database
    engine = create_engine(
        build_sqlalchemy_uri(db_path=db_path).unicode_string(), pool_pre_ping=True
    )
    # attempt to add extension
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        try:
            connection.execute(text("CREATE EXTENSION postgis"))
        except ProgrammingError:
            # extension already exists
            connection.rollback()


def create_test_db(db_path: str) -> None:
    """Create test database if it does not already exist."""
    already_exists = False
    # connect to default "postgres" database
    engine = create_engine(
        build_sqlalchemy_uri(db_path="postgres").unicode_string(), pool_pre_ping=True
    )
    # attempt to create test database
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        try:
            connection.execute(text(f"CREATE DATABASE {db_path}"))
        except ProgrammingError:
            # duplicate database
            already_exists = True
            connection.rollback()

    if not already_exists:
        create_test_db_postgis_extension(db_path=db_path)


def get_geojson_feature_collection(
    geom_type: str,
) -> dict[str, str | FeatureCollection]:
    """Creates a GeoJSON feature collection with single feature of
    the provided geometry type.

    Args:
        geom_type (str): Point, LineString, or Polygon.

    Raises:
        ValueError: Raised if unknown geometry type provided.

    Returns:
        Union[Point, LineString, Polygon]: GeoJSON object of requested geometry type.
    """
    if geom_type.lower() == "point":
        return {
            "layer_name": "Point Example",
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [102.0, 0.5],
                        },
                        "properties": {
                            "prop0": "value0",
                        },
                    }
                ],
            },
        }
    elif geom_type.lower() == "linestring":
        return {
            "layer_name": "Linestring Example",
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                [102.0, 0.0],
                                [103.0, 1.0],
                                [104.0, 0.0],
                                [105.0, 1.0],
                            ],
                        },
                        "properties": {"prop0": "value0", "prop1": 0.0},
                    }
                ],
            },
        }
    elif geom_type.lower() == "polygon":
        return {
            "layer_name": "Polygon Example",
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [100.0, 0.0],
                                    [101.0, 0.0],
                                    [101.0, 1.0],
                                    [100.0, 1.0],
                                    [100.0, 0.0],
                                ],
                            ],
                        },
                        "properties": {
                            "prop0": "value0",
                            "prop1": {
                                "this": "that",
                            },
                        },
                    }
                ],
            },
        }
    elif geom_type.lower() == "multipoint":
        return {
            "layer_name": "Multipoint Example",
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [102.0, 0.5],
                        },
                        "properties": {
                            "prop0": "value0",
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [103.0, 1.0],
                        },
                        "properties": {
                            "prop0": "value1",
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [104.0, 1.5],
                        },
                        "properties": {
                            "prop0": "value2",
                        },
                    },
                ],
            },
        }
    else:
        raise ValueError(f"Unknown geometry type provided: {geom_type}")
