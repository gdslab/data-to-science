from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Optional, Tuple
from uuid import UUID
import re

import geopandas as gpd
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.types import Scope, Receive, Send
from sqlalchemy.orm import Session

from app.utils.staticfiles import RangedStaticFiles

from app import crud
from app.api.deps import can_read_project
from app.api.utils import save_vector_layer_parquet, get_static_dir
from app.core import security
from app.db.session import SessionLocal
from app.models.data_product import DataProduct
from app.models.raw_data import RawData
from app.schemas.api_key import APIKeyUpdate


def parse_vector_parquet_path(path: str) -> Optional[Tuple[UUID, str]]:
    """Parse vector parquet path to extract project_id and layer_id.

    Expected path format: /static/projects/{uuid}/vector/{layer_id}/{layer_id}.parquet

    Args:
        path: URL path to parse

    Returns:
        Tuple of (project_id, layer_id) if valid parquet path, None otherwise
    """
    # Pattern to match: /static/projects/{uuid}/vector/{layer_id}/{layer_id}.parquet
    pattern = r"/static/projects/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/vector/([^/]+)/\2\.parquet"
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
        try:
            request_path = Path(request.url.path)
            data_product_id = UUID(request_path.parents[1].name)
        except (IndexError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="data product not found"
            )
        file_permission = crud.file_permission.get_by_data_product(
            SessionLocal(), file_id=data_product_id
        )
        # public, return file
        if file_permission and file_permission.is_public:
            return

    # check if access to requested data product is restricted or public
    if "data_products" in request.url.path and "colorbars" not in request.url.path:
        try:
            request_path = Path(request.url.path.split("data_products")[1])
            data_product_id = UUID(request_path.parents[-2].name)
            data_product = crud.data_product.get(SessionLocal(), id=data_product_id)
        except (IndexError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="data product not found"
            )

        if not data_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="data product not found"
            )

        if "API_KEY" in request.query_params:
            api_key = request.query_params["API_KEY"]
            # check if owner of api key has access to requested static file
            if verify_api_key_static_file_access(data_product, api_key):
                return

        file_permission = crud.file_permission.get_by_data_product(
            SessionLocal(), file_id=data_product_id
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

    # check if access to requested raw data is restricted or public
    if "raw_data" in request.url.path:
        try:
            request_path = Path(request.url.path.split("raw_data")[1])
            raw_data_id = UUID(request_path.parents[-2].name)
            raw_data = crud.raw_data.get(SessionLocal(), id=raw_data_id)
        except (IndexError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="raw data not found"
            )

        if not raw_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="raw data not found"
            )

        if "API_KEY" in request.query_params:
            api_key = request.query_params["API_KEY"]
            # check if owner of api key has access to requested static file
            if verify_api_key_raw_data_access(raw_data, api_key):
                return

        file_permission = crud.file_permission.get_by_raw_data(
            SessionLocal(), raw_data_id=raw_data_id
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

    # restricted access authorization
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # Extract token from "Bearer <token>" format
    token = access_token.split(" ")[1]

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
    if "projects" in request.url.path:
        try:
            project_id = request.url.path.split("/projects/")[1].split("/")[0]
            project_id_uuid = UUID(project_id)
        except (IndexError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="project not found"
            )
        try:
            project = crud.project.get_user_project(
                SessionLocal(), user_id=user.id, project_id=project_id_uuid
            )
            assert project
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="unable to load project"
            )
        if project["response_code"] != status.HTTP_200_OK:
            raise HTTPException(
                status_code=project["response_code"], detail=project["message"]
            )
    elif "users" in request.url.path:
        try:
            user_id_in_url = request.url.path.split("/users/")[1].split("/")[0]
        except (IndexError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
            )
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
                static_dir, "projects", str(project_id), "vector", layer_id, f"{layer_id}.parquet"
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
                            content={"detail": "Vector layer not found"}
                        )
                        await response(scope, receive, send)
                        return

                except Exception as e:
                    # Error generating parquet
                    response = JSONResponse(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        content={"detail": f"Error generating parquet file: {str(e)}"}
                    )
                    await response(scope, receive, send)
                    return
                finally:
                    db.close()

        await super().__call__(scope, receive, send)
