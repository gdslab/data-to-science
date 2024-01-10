from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings


router = APIRouter()


def get_current_user_for_public_endpoint(
    db: Session = Depends(deps.get_db), token: str = Depends(deps.reusable_oauth2)
) -> models.User | None:
    token_data = deps.decode_jwt(token)
    if token_data.sub:
        user = crud.user.get_by_id(db, user_id=token_data.sub)
        if crud.user.is_email_confirmed(user) and crud.user.is_approved(user):
            return user
    return None


@router.get("", response_model=schemas.DataProduct)
def read_data_public_data_product(
    request: Request,
    file_id: str,
    current_user: models.User = Depends(get_current_user_for_public_endpoint),
    db: Session = Depends(deps.get_db),
) -> Any:
    if request.client and request.client.host == "testclient":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR

    user_id = None
    if current_user:
        user_id = current_user.id
    # returns data product if it is public or accessible by logged in user
    data_product = crud.data_product.get_public_data_product_by_id(
        db, file_id=file_id, upload_dir=upload_dir, user_id=user_id
    )
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )

    return data_product
