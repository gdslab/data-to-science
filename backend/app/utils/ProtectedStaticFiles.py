from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Optional, Tuple
from uuid import UUID
import re
import logging

import geopandas as gpd
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.types import Scope, Receive, Send
from sqlalchemy.orm import Session

from app.utils.staticfiles import RangedStaticFiles

from app import crud
from app.api.deps import can_read_project
from app.api.utils import (
    save_vector_layer_parquet,
    save_vector_layer_flatgeobuf,
    get_static_dir,
)
from app.core import security
from app.db.session import SessionLocal
from app.models.data_product import DataProduct
from app.models.raw_data import RawData
from app.schemas.api_key import APIKeyUpdate

logger = logging.getLogger(__name__)


def validate_and_extract_uuid(path_segment: str) -> UUID:
    """Safely extract and validate UUID from path segment.

    Args:
        path_segment: Path segment that should contain a UUID

    Returns:
        Validated UUID object

    Raises:
        HTTPException: If path segment is invalid or contains traversal sequences
    """
    # Check for path traversal attempts
    if ".." in path_segment or "/" in path_segment or "\\" in path_segment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path"
        )

    # Validate UUID format
    try:
        return UUID(path_segment)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid resource identifier"
        )


def safe_path_split(url_path: str, delimiter: str, index: int) -> str:
    """Safely split URL path and extract component at index.

    Args:
        url_path: URL path to split
        delimiter: String to split on
        index: Index of component to extract

    Returns:
        Path component at specified index

    Raises:
        HTTPException: If split operation fails or index is out of range
    """
    try:
        parts = url_path.split(delimiter)
        if index >= len(parts) or index < 0:
            raise IndexError("Invalid path structure")
        component = parts[index]

        # Check for path traversal in component
        if ".." in component:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path"
            )

        return component
    except (IndexError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )


def extract_bearer_token(auth_header: Optional[str]) -> str:
    """Safely extract token from Bearer authentication header.

    Args:
        auth_header: Authorization header value (e.g., "Bearer <token>")

    Returns:
        Extracted token string

    Raises:
        HTTPException: If header is missing or malformed
    """
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = auth_header[7:]  # len("Bearer ") = 7
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return token


def parse_vector_parquet_path(path: str) -> Optional[Tuple[UUID, str]]:
    """Parse vector parquet path to extract project_id and layer_id.

    Expected path format: /static/projects/{uuid}/vector/{layer_id}/{layer_id}.parquet

    Args:
        path: URL path to parse

    Returns:
        Tuple of (project_id, layer_id) if valid parquet path, None otherwise
    """
    # Strict validation: layer_id must be exactly 11 base64url characters
    # matching the format from generate_unique_id() ([A-Za-z0-9_-]{11})
    # Both directory name and filename (without extension) must match
    pattern = r"/static/projects/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/vector/([A-Za-z0-9_-]{11})/\2\.parquet"
    match = re.match(pattern, path, re.IGNORECASE)

    if match:
        try:
            project_id = UUID(match.group(1))
            layer_id = match.group(2)
            return (project_id, layer_id)
        except ValueError:
            return None

    return None


def parse_vector_flatgeobuf_path(path: str) -> Optional[Tuple[UUID, str]]:
    """Parse vector FlatGeobuf path to extract project_id and layer_id.

    Expected path format: /static/projects/{uuid}/vector/{layer_id}/{layer_id}.fgb

    Args:
        path: URL path to parse

    Returns:
        Tuple of (project_id, layer_id) if valid FlatGeobuf path, None otherwise
    """
    # Strict validation: layer_id must be exactly 11 base64url characters
    # matching the format from generate_unique_id() ([A-Za-z0-9_-]{11})
    # Both directory name and filename (without extension) must match
    pattern = r"/static/projects/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/vector/([A-Za-z0-9_-]{11})/\2\.fgb"
    match = re.match(pattern, path, re.IGNORECASE)

    if match:
        try:
            project_id = UUID(match.group(1))
            layer_id = match.group(2)
            return (project_id, layer_id)
        except ValueError:
            return None

    return None


def verify_api_key_static_file_access(
    data_product: DataProduct, api_key: str, db: Session | None = None
) -> bool:
    """Verify if user associated with API key is authorized to access the
    requested data product.

    Args:
        data_product (DataProduct): Data product that was requested.
        api_key (str): API key included in request.

    Returns:
        _type_: True if authorized to access, False otherwise.
    """
    # check if data product is active
    if not data_product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    # create database session
    if not db:
        db = SessionLocal()
    # get api key db obj
    api_key_obj = crud.api_key.get_by_api_key(db, api_key)

    if api_key_obj:
        # user associated with api key
        user = api_key_obj.owner
        # flight associated with data product
        flight = crud.flight.get(db, id=data_product.flight_id)
        # check if can read flight
        if flight and can_read_project(
            db=db, project_id=flight.project_id, current_user=user
        ):
            # update last accessed date and total requests
            api_key_in = APIKeyUpdate(
                last_used_at=datetime.now(timezone.utc),
                total_requests=api_key_obj.total_requests + 1,
            )
            crud.api_key.update(db, db_obj=api_key_obj, obj_in=api_key_in)
            return True

    return False


def verify_api_key_raw_data_access(
    raw_data: RawData, api_key: str, db: Session | None = None
) -> bool:
    """Verify if user associated with API key is authorized to access the
    requested raw data.

    Args:
        raw_data (RawData): Raw data that was requested.
        api_key (str): API key included in request.
        db (Session | None): Database session. If None, a new session is created.

    Returns:
        bool: True if authorized to access, False otherwise.
    """
    # check if raw data is active
    if not raw_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Raw data not found"
        )
    # create database session
    if not db:
        db = SessionLocal()
    # get api key db obj
    api_key_obj = crud.api_key.get_by_api_key(db, api_key)

    if api_key_obj:
        # user associated with api key
        user = api_key_obj.owner
        # flight associated with raw data
        flight = crud.flight.get(db, id=raw_data.flight_id)
        # check if can read flight
        if flight and can_read_project(
            db=db, project_id=flight.project_id, current_user=user
        ):
            # update last accessed date and total requests
            api_key_in = APIKeyUpdate(
                last_used_at=datetime.now(timezone.utc),
                total_requests=api_key_obj.total_requests + 1,
            )
            crud.api_key.update(db, db_obj=api_key_obj, obj_in=api_key_in)
            return True

    return False


async def verify_static_file_access(request: Request) -> None:
    """
    Verify if requested static file has restricted or unrestricted access. If
    restricted, verify client requesting a static file has access to the project
    associated with the file.

    Args:
        request (Request): Client request for a static file

    Raises:
        HTTPException: Client not authenticated
        HTTPException: User associated with access token not found
        HTTPException: User does not have access to project
    """
    # check if access to color bar's data product is restricted or public
    if "colorbars" in request.url.path:
        request_path = Path(request.url.path)
        try:
            # Get the parent directory name (should be data product ID)
            parent_name = request_path.parents[1].name
        except IndexError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="data product not found"
            )

        # Validate and extract UUID
        data_product_id = validate_and_extract_uuid(parent_name)
        db = SessionLocal()
        try:
            file_permission = crud.file_permission.get_by_data_product(
                db, file_id=data_product_id
            )
            # public, return file
            if file_permission and file_permission.is_public:
                return
        finally:
            db.close()

    # check if access to requested data product is restricted or public
    if "data_products" in request.url.path and "colorbars" not in request.url.path:
        # Split path and get the portion after "data_products"
        path_after_dp = safe_path_split(request.url.path, "data_products", 1)
        request_path = Path(path_after_dp)
        try:
            # Get the parent directory name (should be data product ID)
            parent_name = request_path.parents[-2].name
        except IndexError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="data product not found"
            )

        # Validate and extract UUID
        data_product_id = validate_and_extract_uuid(parent_name)

        db = SessionLocal()
        try:
            data_product = crud.data_product.get(db, id=data_product_id)

            if not data_product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="data product not found",
                )

            # Check for API key in header (preferred) or query param (legacy/QGIS)
            api_key = request.headers.get("X-API-KEY") or request.query_params.get(
                "API_KEY"
            )
            if api_key:
                # check if owner of api key has access to requested static file
                if verify_api_key_static_file_access(data_product, api_key, db):
                    return

            file_permission = crud.file_permission.get_by_data_product(
                db, file_id=data_product_id
            )
            # if file is deactivated return 404
            if file_permission and file_permission.file.is_active is False:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="data product not found",
                )
            # public, return file
            if file_permission and file_permission.is_public:
                return

            # NOTE: If file_permission is None or not public, we intentionally
            # fall through to project-level authentication below. This ensures
            # files without explicit public permissions require full authentication.
        finally:
            db.close()

    # check if access to requested raw data is restricted or public
    if "raw_data" in request.url.path:
        # Split path and get the portion after "raw_data"
        path_after_rd = safe_path_split(request.url.path, "raw_data", 1)
        request_path = Path(path_after_rd)
        try:
            # Get the parent directory name (should be raw data ID)
            parent_name = request_path.parents[-2].name
        except IndexError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="raw data not found"
            )

        # Validate and extract UUID
        raw_data_id = validate_and_extract_uuid(parent_name)

        db = SessionLocal()
        try:
            raw_data = crud.raw_data.get(db, id=raw_data_id)

            if not raw_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="raw data not found"
                )

            # Check for API key in header (preferred) or query param (legacy/QGIS)
            api_key = request.headers.get("X-API-KEY") or request.query_params.get(
                "API_KEY"
            )
            if api_key:
                # check if owner of api key has access to requested static file
                if verify_api_key_raw_data_access(raw_data, api_key, db):
                    return

            file_permission = crud.file_permission.get_by_raw_data(
                db, raw_data_id=raw_data_id
            )
            # if file is deactivated return 404
            if file_permission and file_permission.raw_data.is_active is False:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="raw data not found",
                )
            # public, return file
            if file_permission and file_permission.is_public:
                return

            # NOTE: If file_permission is None or not public, we intentionally
            # fall through to project-level authentication below. This ensures
            # files without explicit public permissions require full authentication.
        finally:
            db.close()

    # Handle project-scoped files (vector data, previews, etc.)
    if "projects" in request.url.path and "indoor_projects" not in request.url.path:
        # Safely extract project ID from URL
        project_id_str = safe_path_split(request.url.path, "/projects/", 1)
        project_id_str = safe_path_split(project_id_str, "/", 0)
        project_id_uuid = validate_and_extract_uuid(project_id_str)

        # Check for API_KEY authentication (for programmatic access, QGIS, etc.)
        # Support both header (preferred) and query param (legacy/QGIS)
        api_key = request.headers.get("X-API-KEY") or request.query_params.get(
            "API_KEY"
        )
        if api_key:
            db = SessionLocal()
            try:
                api_key_obj = crud.api_key.get_by_api_key(db, api_key)
                if api_key_obj:
                    user_from_api_key = api_key_obj.owner
                    if can_read_project(
                        db=db,
                        project_id=project_id_uuid,
                        current_user=user_from_api_key,
                    ):
                        # Update API key usage stats
                        api_key_in = APIKeyUpdate(
                            last_used_at=datetime.now(timezone.utc),
                            total_requests=api_key_obj.total_requests + 1,
                        )
                        crud.api_key.update(db, db_obj=api_key_obj, obj_in=api_key_in)
                        return  # Authorized via API key
            finally:
                db.close()

        # Fall back to JWT token authentication (for browser-based access)
        access_token = request.cookies.get("access_token")
        token = extract_bearer_token(access_token)

        # Validate token and get payload
        payload = security.validate_token_and_get_payload(token, "access")

        # Get user from payload
        db = SessionLocal()
        try:
            user = security.get_user_from_token_payload(db, payload)
        finally:
            db.close()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
            )

        db_project = SessionLocal()
        try:
            project = crud.project.get_user_project(
                db_project, user_id=user.id, project_id=project_id_uuid
            )
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="project not found"
                )
            if project["response_code"] != status.HTTP_200_OK:
                raise HTTPException(
                    status_code=project["response_code"], detail=project["message"]
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="unable to load project"
            )
        finally:
            db_project.close()
    elif "users" in request.url.path:
        # Users path requires JWT authentication
        access_token = request.cookies.get("access_token")
        token = extract_bearer_token(access_token)

        # Validate token and get payload
        payload = security.validate_token_and_get_payload(token, "access")

        # Get user from payload
        db = SessionLocal()
        try:
            user = security.get_user_from_token_payload(db, payload)
        finally:
            db.close()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
            )

        # Validate user ID in URL (safe_path_split handles traversal checks)
        user_id_str = safe_path_split(request.url.path, "/users/", 1)
        user_id_str = safe_path_split(user_id_str, "/", 0)
    elif "indoor_projects" in request.url.path:
        # Safely extract indoor project ID from URL
        indoor_project_id_str = safe_path_split(
            request.url.path, "/indoor_projects/", 1
        )
        indoor_project_id_str = safe_path_split(indoor_project_id_str, "/", 0)
        indoor_project_id_uuid = validate_and_extract_uuid(indoor_project_id_str)

        # Indoor projects require JWT authentication
        access_token = request.cookies.get("access_token")
        token = extract_bearer_token(access_token)

        # Validate token and get payload
        payload = security.validate_token_and_get_payload(token, "access")

        # Get user from payload
        db = SessionLocal()
        try:
            user = security.get_user_from_token_payload(db, payload)
        finally:
            db.close()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
            )

        # Verify user has access to indoor project
        db_indoor = SessionLocal()
        try:
            try:
                indoor_project = crud.indoor_project.get_with_permission(
                    db_indoor,
                    indoor_project_id=indoor_project_id_uuid,
                    user_id=user.id,
                )
            except Exception:
                # User doesn't have permission or project doesn't exist
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="indoor project not found",
                )
        finally:
            db_indoor.close()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


class ProtectedStaticFiles(RangedStaticFiles):
    """Extend StatcFiles to include user access authorization."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "http"

        request = Request(scope, receive)
        await verify_static_file_access(request)

        # Check if this is a request for a vector parquet file
        parsed_path = parse_vector_parquet_path(request.url.path)
        if parsed_path and request.url.path.endswith(".parquet"):
            project_id, layer_id = parsed_path
            static_dir = get_static_dir()
            parquet_path = os.path.join(
                static_dir,
                "projects",
                str(project_id),
                "vector",
                layer_id,
                f"{layer_id}.parquet",
            )

            # If parquet file doesn't exist, generate it on-demand
            if not os.path.exists(parquet_path):
                db = SessionLocal()
                try:
                    # Verify layer exists in database
                    features = crud.vector_layer.get_vector_layer_by_id(
                        db, project_id=project_id, layer_id=layer_id
                    )

                    if features:
                        # Convert features to GeoDataFrame and generate parquet
                        gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
                        save_vector_layer_parquet(project_id, layer_id, gdf, static_dir)
                    else:
                        # Layer not found in database
                        response = JSONResponse(
                            status_code=status.HTTP_404_NOT_FOUND,
                            content={"detail": "Vector layer not found"},
                        )
                        await response(scope, receive, send)
                        return

                except Exception as e:
                    # Error generating parquet - log details but don't expose to client
                    logger.error(
                        f"Error generating parquet file for project {project_id}, layer {layer_id}: {str(e)}",
                        exc_info=True,
                    )
                    response = JSONResponse(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        content={"detail": "Error processing request"},
                    )
                    await response(scope, receive, send)
                    return
                finally:
                    db.close()

        # Check if this is a request for a vector FlatGeobuf file
        parsed_fgb_path = parse_vector_flatgeobuf_path(request.url.path)
        if parsed_fgb_path and request.url.path.endswith(".fgb"):
            project_id, layer_id = parsed_fgb_path
            static_dir = get_static_dir()
            fgb_path = os.path.join(
                static_dir,
                "projects",
                str(project_id),
                "vector",
                layer_id,
                f"{layer_id}.fgb",
            )

            # If FlatGeobuf file doesn't exist, generate it on-demand
            if not os.path.exists(fgb_path):
                db = SessionLocal()
                try:
                    # Verify layer exists in database
                    features = crud.vector_layer.get_vector_layer_by_id(
                        db, project_id=project_id, layer_id=layer_id
                    )

                    if features:
                        # Convert features to GeoDataFrame and generate FlatGeobuf
                        gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
                        save_vector_layer_flatgeobuf(
                            project_id, layer_id, gdf, static_dir
                        )
                    else:
                        # Layer not found in database
                        response = JSONResponse(
                            status_code=status.HTTP_404_NOT_FOUND,
                            content={"detail": "Vector layer not found"},
                        )
                        await response(scope, receive, send)
                        return

                except Exception as e:
                    # Error generating FlatGeobuf - log details but don't expose to client
                    logger.error(
                        f"Error generating FlatGeobuf file for project {project_id}, layer {layer_id}: {str(e)}",
                        exc_info=True,
                    )
                    response = JSONResponse(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        content={"detail": "Error processing request"},
                    )
                    await response(scope, receive, send)
                    return
                finally:
                    db.close()

        await super().__call__(scope, receive, send)
