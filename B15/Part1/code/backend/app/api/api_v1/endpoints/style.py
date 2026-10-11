from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.UserStyle)
def create_user_style(
    data_product_id: UUID,
    user_style_in: schemas.UserStyleCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: models.Flight = Depends(deps.can_read_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create user style settings for a data product."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    existing_user_style = crud.user_style.get_by_data_product_and_user(
        db, data_product_id=data_product_id, user_id=current_user.id
    )
    if existing_user_style:
        raise HTTPException(
            status_code=status.HTTP_400_NOT_FOUND, detail="User style already exists"
        )
    user_style = crud.user_style.create_with_data_product_and_user(
        db,
        obj_in=user_style_in,
        data_product_id=data_product_id,
        user_id=current_user.id,
    )
    return user_style


@router.put("", response_model=schemas.UserStyle)
def update_user_style(
    data_product_id: UUID,
    user_style_in: schemas.UserStyleUpdate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    flight: models.Flight = Depends(deps.can_read_flight),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update user's style settings for a data product."""
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    current_user_style = crud.user_style.get_by_data_product_and_user(
        db, data_product_id=data_product_id, user_id=current_user.id
    )
    if not current_user_style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User style not found"
        )
    updated_user_style = crud.user_style.update(
        db, db_obj=current_user_style, obj_in=user_style_in
    )
    return updated_user_style
