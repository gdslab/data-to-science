from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.core.config import settings
from app.utils.ColorBar import ColorBar

router = APIRouter()


@router.get("/colorbar")
def get_colorbar_for_data_product_with_public_access(
    request: Request,
    cmin: int | float,
    cmax: int | float,
    cmap: str,
    project_id: UUID,
    flight_id: UUID,
    data_product_id: UUID,
    db: Session = Depends(deps.get_db),
) -> Any:
    if request.client and request.client.host == "testclient":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR
    data_product = crud.data_product.get_public_data_product_by_id(
        db, file_id=data_product_id, upload_dir=upload_dir
    )
    if not data_product:
        path_params = request.path_params
        query_params = request.query_params
        return RedirectResponse(f"colorbar/user_access?{query_params}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    if data_product.data_type != "dsm":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Colorbars only available for DSM data products",
        )

    if request.client and request.client.host == "testclient":
        output_dir = f"{settings.TEST_STATIC_DIR}/projects/{project_id}/flights/{flight_id}/dsm/colorbars/{data_product_id}"
    else:
        output_dir = f"{settings.STATIC_DIR}/projects/{project_id}/flights/{flight_id}/dsm/colorbars/{data_product_id}"

    try:
        colorbar = ColorBar(cmin=cmin, cmax=cmax, outpath=output_dir, cmap=cmap)
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

    if request.client and request.client.host == "testclient":
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
    if data_product.data_type != "dsm":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Colorbars only available for DSM data products",
        )

    if request.client and request.client.host == "testclient":
        output_dir = f"{settings.TEST_STATIC_DIR}/projects/{project.id}/flights/{flight.id}/dsm/colorbars/{data_product_id}"
    else:
        output_dir = f"{settings.STATIC_DIR}/projects/{project.id}/flights/{flight.id}/dsm/colorbars/{data_product_id}"

    try:
        colorbar = ColorBar(cmin=cmin, cmax=cmax, outpath=output_dir, cmap=cmap)
        colorbar_url = colorbar.generate_colorbar()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"colorbar_url": colorbar_url}
