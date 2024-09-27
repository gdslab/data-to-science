import os
from io import BytesIO
from typing import Annotated, Any, List, Optional

import httpx
import rasterio
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import UUID4
from rasterio.warp import transform_bounds
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings


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
):
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
):
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

    # request map tile from titiler
    async with httpx.AsyncClient() as client:
        tile_url = (
            f"http://varnish/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@{scale}x"
            f"?url={data_product.filepath}{query_params}"
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
def read_data_product_bounds(
    request: Request,
    data_product_id: UUID4,
    current_user: Optional[models.User] = Depends(deps.get_optional_current_user),
    db: Session = Depends(deps.get_db),
):
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
