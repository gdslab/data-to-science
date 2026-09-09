import base64
import hashlib
import hmac
import time
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import rasterio
from affine import Affine
from faker import Faker
from geojson_pydantic import Feature, FeatureCollection, LineString, Point, Polygon
from pydantic import PostgresDsn
from rasterio.enums import ColorInterp
from rasterio.transform import from_origin
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.config import settings

faker = Faker()


class VectorLayerDict(TypedDict):
    layer_name: str
    geojson: Dict[str, Any]


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


def expected_tile_signature(expires: int, payload: str) -> str:
    """Recreate the signature varnish computes for a tile request.

    Mirrors the HMAC in varnish/default.vcl so tests fail if the payload the
    backend signs stops matching the one varnish verifies.

    Args:
        expires (int): Expiration timestamp from the tile URL.
        payload (str): Signed payload following the timestamp.

    Returns:
        str: Expected value of the `secure` query param.
    """
    digest = hmac.new(
        base64.b64decode(settings.TILE_SIGNING_SECRET_KEY),
        f"{expires}{payload}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"0x{digest}"


def mock_async_http_client(
    mock_async_client_cls: MagicMock,
    response: Optional[MagicMock] = None,
    side_effect: Optional[Exception] = None,
) -> AsyncMock:
    """Wire an AsyncMock httpx client onto a patched httpx.AsyncClient class.

    Args:
        mock_async_client_cls (MagicMock): Patched ``httpx.AsyncClient`` class.
        response (Optional[MagicMock]): Response returned by ``client.get``.
        side_effect (Optional[Exception]): Exception raised by ``client.get``.

    Returns:
        AsyncMock: Client yielded by ``async with httpx.AsyncClient()``.
    """
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=response, side_effect=side_effect)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client
    return mock_client


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


def create_test_db(db_path: str, max_retries: int = 5) -> None:
    """Create test database if it does not already exist.

    Retries on transient lock contention, which can occur when several
    pytest-xdist workers issue ``CREATE DATABASE`` against the shared template
    database at the same time.
    """
    already_exists = False
    # connect to default "postgres" database
    engine = create_engine(
        build_sqlalchemy_uri(db_path="postgres").unicode_string(), pool_pre_ping=True
    )
    # attempt to create test database, retrying on transient lock contention
    for attempt in range(max_retries):
        try:
            with engine.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            ) as connection:
                connection.execute(text(f"CREATE DATABASE {db_path}"))
            break
        except ProgrammingError:
            # duplicate database
            already_exists = True
            break
        except OperationalError:
            # template database temporarily locked by a concurrent worker
            if attempt == max_retries - 1:
                raise
            time.sleep(0.5 * (attempt + 1))

    if not already_exists:
        create_test_db_postgis_extension(db_path=db_path)


def get_geojson_feature_collection(
    geom_type: str,
) -> VectorLayerDict:
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
            "geojson": FeatureCollection[Feature[Point, Dict[str, object]]](
                type="FeatureCollection",
                features=[
                    Feature[Point, Dict[str, object]](
                        type="Feature",
                        geometry={
                            "type": "Point",
                            "coordinates": [102.0, 0.5],
                        },
                        properties={
                            "prop0": "value0",
                        },
                    )
                ],
            ).model_dump(),
        }
    elif geom_type.lower() == "linestring":
        return {
            "layer_name": "Linestring Example",
            "geojson": FeatureCollection[Feature[LineString, Dict[str, object]]](
                type="FeatureCollection",
                features=[
                    Feature[LineString, Dict[str, object]](
                        type="Feature",
                        geometry={
                            "type": "LineString",
                            "coordinates": [
                                [102.0, 0.0],
                                [103.0, 1.0],
                                [104.0, 0.0],
                                [105.0, 1.0],
                            ],
                        },
                        properties={"prop0": "value0", "prop1": 0.0},
                    )
                ],
            ).model_dump(),
        }
    elif geom_type.lower() == "polygon":
        return {
            "layer_name": "Polygon Example",
            "geojson": FeatureCollection[Feature[Polygon, Dict[str, object]]](
                type="FeatureCollection",
                features=[
                    Feature[Polygon, Dict[str, object]](
                        type="Feature",
                        geometry={
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
                        properties={
                            "prop0": "value0",
                            "prop1": {
                                "this": "that",
                            },
                        },
                    )
                ],
            ).model_dump(),
        }
    elif geom_type.lower() == "multipoint":
        return {
            "layer_name": "Multipoint Example",
            "geojson": FeatureCollection[Feature[Point, Dict[str, object]]](
                type="FeatureCollection",
                features=[
                    Feature[Point, Dict[str, object]](
                        type="Feature",
                        geometry={
                            "type": "Point",
                            "coordinates": [102.0, 0.5],
                        },
                        properties={
                            "prop0": "value0",
                        },
                    ),
                    Feature[Point, Dict[str, object]](
                        type="Feature",
                        geometry={
                            "type": "Point",
                            "coordinates": [103.0, 1.0],
                        },
                        properties={
                            "prop0": "value0",
                        },
                    ),
                    Feature[Point, Dict[str, object]](
                        type="Feature",
                        geometry={
                            "type": "Point",
                            "coordinates": [104.0, 1.5],
                        },
                        properties={
                            "prop0": "value0",
                        },
                    ),
                ],
            ).model_dump(),
        }
    elif geom_type.lower() == "too_many_features":
        return {
            "layer_name": "Point Example",
            "geojson": FeatureCollection[Feature[Point, Dict[str, object]]](
                type="FeatureCollection",
                features=[
                    Feature[Point, Dict[str, object]](
                        type="Feature",
                        geometry={
                            "type": "Point",
                            "coordinates": [102.0, 0.5],
                        },
                        properties={
                            "prop0": "value0",
                        },
                    )
                ]
                * 250001,
            ).model_dump(),
        }
    elif geom_type.lower() == "invalid_longitude":
        return {
            "layer_name": "Invalid Longitude Example",
            "geojson": FeatureCollection[Feature[Point, Dict[str, object]]](
                type="FeatureCollection",
                features=[
                    Feature[Point, Dict[str, object]](
                        type="Feature",
                        geometry={
                            "type": "Point",
                            "coordinates": [200.0, 0.5],  # Invalid longitude
                        },
                        properties={
                            "prop0": "value0",
                        },
                    )
                ],
            ).model_dump(),
        }
    elif geom_type.lower() == "invalid_latitude":
        return {
            "layer_name": "Invalid Latitude Example",
            "geojson": FeatureCollection[Feature[Point, Dict[str, object]]](
                type="FeatureCollection",
                features=[
                    Feature[Point, Dict[str, object]](
                        type="Feature",
                        geometry={
                            "type": "Point",
                            "coordinates": [102.0, 95.0],  # Invalid latitude
                        },
                        properties={
                            "prop0": "value0",
                        },
                    )
                ],
            ).model_dump(),
        }
    elif geom_type.lower() == "empty_features":
        return {
            "layer_name": "Empty Features Example",
            "geojson": FeatureCollection[Feature[Point, Dict[str, object]]](
                type="FeatureCollection",
                features=[],
            ).model_dump(),
        }
    else:
        raise ValueError(f"Unknown geometry type provided: {geom_type}")


def write_raster_without_stats(
    path: Path,
    count: int = 1,
    crs: str | None = "EPSG:32616",
    transform: Affine | None = None,
    dtype: str = "uint16",
) -> Path:
    """Writes a small raster that has no precomputed statistics."""
    data = np.arange(count * 64 * 64, dtype=dtype).reshape(count, 64, 64)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=64,
        width=64,
        count=count,
        dtype=dtype,
        crs=crs,
        transform=transform or from_origin(0, 64, 1, 1),
    ) as dst:
        dst.write(data)

    return path


def write_gray_alpha_raster(
    path: Path,
    size: int = 64,
    dtype: str = "float32",
    crs: str = "EPSG:32616",
    transform: Affine | None = None,
) -> Path:
    """Writes a two band raster, data plus alpha, with its top half transparent.

    Integer alpha bands are opaque at the type's maximum, as GDAL writes them.
    Floating point alpha bands are opaque at 255, as GDAL's warper writes them.
    """
    data = np.linspace(15.0, 45.0, size * size).astype(dtype).reshape(1, size, size)
    opaque = np.iinfo(dtype).max if np.issubdtype(np.dtype(dtype), np.integer) else 255
    alpha = np.full((1, size, size), opaque, dtype=dtype)
    alpha[:, : size // 2, :] = 0

    # GTiff records the alpha flag in its EXTRASAMPLES tag, which is fixed at
    # creation, so assigning colorinterp to an open dataset alone does not stick.
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=size,
        width=size,
        count=2,
        dtype=dtype,
        crs=crs,
        transform=transform or from_origin(0, size, 1, 1),
        alpha="YES",
    ) as dst:
        dst.write(np.concatenate([data, alpha]))
        dst.colorinterp = [ColorInterp.gray, ColorInterp.alpha]

    return path
