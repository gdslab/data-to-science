from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings


router = APIRouter()


@router.get("", response_model=schemas.DataProduct)
def read_shared_data_product_with_public_access(
    request: Request,
    file_id: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    if request.client and request.client.host == "testclient":
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
    file_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_approved_user),
):
    if request.client and request.client.host == "testclient":
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
