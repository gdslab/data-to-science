import os
import urllib.parse
from io import BytesIO
from typing import Annotated, Any, List, Optional, Sequence, Union
from uuid import UUID

import httpx
import rasterio
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse, StreamingResponse
from geojson_pydantic import FeatureCollection
from pydantic import UUID4
from rasterio.warp import transform_bounds
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.utils import get_signature_for_data_product
from app.core.config import settings
from app.core.limiter import limiter


router = APIRouter()


@router.get("", response_model=schemas.DataProduct)
def read_shared_data_product_with_public_access(
    request: Request,
    file_id: UUID4,
    db: Session = Depends(deps.get_db),
) -> Any:
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR

    data_product = crud.data_product.get_public_data_product_by_id(
        db, file_id=file_id, upload_dir=upload_dir
    )
    if not data_product:
        return RedirectResponse(f"public/user_access?file_id={file_id}")

    return data_product


@router.get("/user_access", response_model=schemas.DataProduct)
def read_shared_data_product_with_user_access(
    request: Request,
    file_id: UUID4,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_approved_user),
) -> Any:
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR

    data_product = crud.data_product.get_public_data_product_by_id(
        db, file_id=file_id, upload_dir=upload_dir, user_id=current_user.id
    )
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    return data_product


@router.get("/vectortiles")
async def get_vector_tiles_for_vector_layer(
    x: int,
    y: int,
    z: int,
    layer_id: str,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> StreamingResponse:
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR

    # check if user has access through project member role
    can_access = crud.vector_layer.verify_user_access_to_vector_layer_by_id(
        db, layer_id=layer_id, user_id=current_user.id
    )
    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Unable to view vector layer"
        )

    filter_param = urllib.parse.quote(f"layer_id = '{layer_id}'")
    # request vector tile from pg_tileserv
    async with httpx.AsyncClient() as client:
        tile_url = (
            f"http://varnish/public.vector_layers/{z}/{x}/{y}.pbf?filter={filter_param}"
        )
        # timeout request after 30 seconds
        response = await client.get(tile_url, timeout=30.0)
    if response.status_code == 200:
        return StreamingResponse(
            BytesIO(response.content), media_type="application/vnd.mapbox-vector-tile"
        )
    else:
        raise HTTPException(
            status_code=response.status_code, detail=f"Error: {response.text}"
        )


@router.get("/maptiles")
async def get_map_tiles_for_data_product(
    x: float,
    y: float,
    z: int,
    data_product_id: UUID4,
    scale: int,
    bidx: Annotated[Optional[List[int]], Query()] = None,
    rescale: Annotated[Optional[List[str]], Query()] = None,
    colormap_name: Annotated[Optional[str], Query()] = None,
    current_user: models.User = Depends(deps.get_optional_current_user),
    db: Session = Depends(deps.get_db),
) -> StreamingResponse:
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR

    # get user id if available
    user_id = None
    if current_user:
        user_id = current_user.id

    # check if file is public or if user has access through project member role
    data_product = crud.data_product.get_public_data_product_by_id(
        db, file_id=data_product_id, upload_dir=upload_dir, user_id=user_id
    )
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )

    # construct titiler query params
    query_params = ""
    if bidx and len(bidx) > 0:
        for band_index in bidx:
            query_params += f"&bidx={band_index}"
    if rescale and len(rescale) > 0:
        for rescale_range in rescale:
            query_params += f"&rescale={rescale_range}"
    if colormap_name:
        query_params += f"&colormap_name={colormap_name}"

    # sign varnish request (required by varnish/default.vcl)
    signature, expiration = get_signature_for_data_product(data_product_id)

    # request map tile from titiler
    async with httpx.AsyncClient() as client:
        tile_url = (
            f"http://varnish/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@{scale}x"
            f"?url={data_product.filepath}"
            f"&dataProductId={data_product_id}"
            f"&expires={expiration}&secure={signature}"
            f"{query_params}"
        )
        # timeout request after 30 seconds
        response = await client.get(tile_url, timeout=30.0)
    if response.status_code == 200:
        return StreamingResponse(BytesIO(response.content), media_type="image/png")
    else:
        raise HTTPException(
            status_code=response.status_code, detail=f"Error: {response.text}"
        )


@router.get("/bounds", response_model=schemas.data_product.DataProductBoundingBox)
@limiter.limit("60/minute")
def read_data_product_bounds(
    request: Request,
    data_product_id: UUID4,
    current_user: Optional[models.User] = Depends(deps.get_optional_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR

    # get user id if available
    user_id = None
    if current_user:
        user_id = current_user.id

    # check if file is public or if user has access through project member role
    data_product = crud.data_product.get_public_data_product_by_id(
        db, file_id=data_product_id, upload_dir=upload_dir, user_id=user_id
    )
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )

    # get bounds and project to wgs84
    try:
        with rasterio.open(data_product.filepath) as dataset:
            bounds = dataset.bounds
            wgs84_bounds = transform_bounds(
                src_crs=dataset.crs,
                dst_crs="EPSG:4326",
                left=bounds.left,
                bottom=bounds.bottom,
                right=bounds.right,
                top=bounds.top,
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to find bounds for data product",
        )

    # return bounds
    return {"bounds": list(wgs84_bounds)}


@router.get(
    "/projects",
    response_model=Union[List[schemas.project.PublishedProjects], FeatureCollection],
)
@limiter.limit("60/minute")
def read_published_projects(
    request: Request,
    has_raster: bool = False,
    format: str = Query("json", pattern="^(json|geojson)$"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve all active published projects. No authentication required."""
    projects = crud.project.get_published_projects(db, has_raster=has_raster)

    if format == "geojson":
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [project.centroid.x, project.centroid.y],
                    },
                    "properties": {
                        "id": str(project.id),
                        "title": project.title,
                        "description": project.description,
                    },
                }
                for project in projects
            ],
        }
    return projects


@router.get(
    "/projects/{project_id}",
    response_model=Union[schemas.project.PublishedProjects, FeatureCollection],
)
@limiter.limit("120/minute")
def read_published_project(
    request: Request,
    project_id: UUID4,
    format: str = Query("json", pattern="^(json|geojson)$"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve a single active published project. No authentication required."""
    project = crud.project.get_published_project_by_id(db, project_id=project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if format == "geojson":
        return {"type": "FeatureCollection", "features": [project.field]}
    return project


@router.get(
    "/projects/{project_id}/flights",
    response_model=Sequence[schemas.Flight],
)
@limiter.limit("120/minute")
def read_published_project_flights(
    request: Request,
    project_id: UUID4,
    has_raster: bool = False,
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve flights and public data products for a published project. No authentication required."""
    project = crud.project.get_published_project_by_id(db, project_id=project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
    return crud.flight.get_public_flights_by_project(
        db, project_id=project_id, upload_dir=upload_dir, has_raster=has_raster
    )


@router.post("/data_products/{data_product_id}/view")
@limiter.limit("60/minute")
def record_public_data_product_view(
    request: Request,
    response: Response,
    data_product_id: UUID,
    session_id: Annotated[Optional[str], Header(alias="X-Session-Id")] = None,
    current_user: Optional[models.User] = Depends(deps.get_optional_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Record an anonymous or authenticated view for a data product.

    Authenticated callers use their user_id. Anonymous callers must supply an
    X-Session-Id header. A view is recorded only when the project is published or
    the caller is a project member. Returns 201 on insert, 200 on dedup-skip,
    400 on missing identity, 404 on not-found or unauthorized.
    """
    data_product = crud.data_product.get(db, id=data_product_id)
    if (
        not data_product
        or not data_product.is_active
        or not data_product.is_initial_processing_completed
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )

    # Require access via publication or project membership for every caller.
    flight = crud.flight.get(db, id=data_product.flight_id)
    project = crud.project.get(db, id=flight.project_id) if flight else None
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )

    is_member = bool(
        current_user
        and crud.project_member.get_by_project_and_member_id(
            db, project_uuid=project.id, member_id=current_user.id
        )
    )
    if not project.is_published and not is_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )

    if not current_user and not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-Id is required for anonymous views",
        )

    user_id = current_user.id if current_user else None
    try:
        view = crud.data_product_view.create_if_not_recent(
            db,
            data_product_id=data_product_id,
            user_id=user_id,
            session_id=session_id,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-Id is required for anonymous views",
        )

    if view:
        response.status_code = status.HTTP_201_CREATED
        return {"message": "View recorded"}
    response.status_code = status.HTTP_200_OK
    return {"message": "View already recorded"}
