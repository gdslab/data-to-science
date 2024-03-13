import os
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.api.api_v1.endpoints.data_products import get_data_product_dir
from app.core.config import settings
from app.utils.ColorBar import ColorBar

router = APIRouter()


def is_singleband(data_product: models.DataProduct) -> bool:
    """Return True if data product is a single band raster.

    Args:
        data_product (models.DataProduct): DataProduct object representing raster.

    Returns:
        bool: True if raster is singleband, False if not raster or multiband.
    """
    if data_product.stac_properties and "raster" in data_product.stac_properties:
        if len(data_product.stac_properties.get("raster", [])) == 1:
            return True
        else:
            return False
    return False


@router.get("/colorbar")
def get_colorbar_for_data_product_with_public_access(
    request: Request,
    cmin: int | float,
    cmax: int | float,
    cmap: str,
    refresh: bool,
    project_id: UUID,
    flight_id: UUID,
    data_product_id: UUID,
    db: Session = Depends(deps.get_db),
) -> Any:
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
    data_product = crud.data_product.get_public_data_product_by_id(
        db, file_id=data_product_id, upload_dir=upload_dir
    )
    if not data_product:
        query_params = request.query_params
        return RedirectResponse(f"colorbar/user_access?{query_params}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    if not is_singleband(data_product):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Colorbars only available for single band data products",
        )
    data_product_dir = get_data_product_dir(
        str(project_id), str(flight_id), str(data_product_id)
    )
    data_product_dir = data_product_dir / "colorbars"

    try:
        colorbar = ColorBar(
            cmin=cmin,
            cmax=cmax,
            outpath=str(data_product_dir),
            cmap=cmap,
            refresh=refresh,
        )
        colorbar_url = colorbar.generate_colorbar()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"colorbar_url": colorbar_url}


@router.get("/colorbar/user_access")
def get_colorbar_for_data_product_with_user_access(
    request: Request,
    cmin: int | float,
    cmax: int | float,
    cmap: str,
    refresh: bool,
    data_product_id: UUID,
    current_user: models.User = Depends(deps.get_current_approved_user),
    project: models.Project = Depends(deps.can_read_project),
    flight: models.Flight = Depends(deps.can_read_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )

    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
    data_product = crud.data_product.get_single_by_id(
        db,
        data_product_id=data_product_id,
        upload_dir=upload_dir,
        user_id=current_user.id,
    )
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )

    if not is_singleband(data_product):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Colorbars only available for DSM data products",
        )

    data_product_dir = get_data_product_dir(
        str(project.id), str(flight.id), str(data_product.id)
    )
    data_product_dir = data_product_dir / "colorbars"

    try:
        colorbar = ColorBar(
            cmin=cmin,
            cmax=cmax,
            outpath=str(data_product_dir),
            cmap=cmap,
            refresh=refresh,
        )
        colorbar_url = colorbar.generate_colorbar()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"colorbar_url": colorbar_url}
