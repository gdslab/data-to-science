from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import Required
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings


router = APIRouter()


@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
    *, 
    db: Session = Depends(deps.get_db),
    password: str = Body(Required),  # TODO add minimal password requirements
    email: EmailStr = Body(Required),
    first_name: str = Body(Required),
    last_name: str = Body(Required),
) -> Any:
    """Create new user with unique email."""
    # check if user with this email already exists
    user = crud.user.get_by_email(db, email=email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="This email address is already in use"  # TODO 
        )
    # create user in database
    user_in = schemas.UserCreate(
        password=password, 
        email=email,
        first_name=first_name,
        last_name=last_name,
    )
    user = crud.user.create(db, obj_in=user_in)
    return user


@router.put("/", response_model=schemas.User)
def update_current_user(
    *,
    password: str = Body(None),
    first_name: str = Body(None),
    last_name: str = Body(None),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update current user."""
    current_user_data = jsonable_encoder(current_user)
    user_in = schemas.UserUpdate(**current_user_data)
    if password is not None:
        user_in.password = password
    if first_name is not None:
        user_in.first_name = first_name
    if last_name is not None:
        user_in.last_name = last_name
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/current", response_model=schemas.User)
def read_current_user(
    *,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve current user."""
    return current_user
