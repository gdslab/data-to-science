from secrets import token_urlsafe
from typing import Annotated, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    status,
    Query,
)
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps, mail
from app.core import security

router = APIRouter()


@router.post("", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    password: str = Body(),  # TODO add minimal password requirements
    email: EmailStr = Body(),
    first_name: str = Body(),
    last_name: str = Body(),
) -> Any:
    """Create new user with unique email."""
    existing_user = crud.user.get_by_email(db, email=email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email address already in use"
        )
    user_in = schemas.UserCreate(
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name,
    )
    user = crud.user.create(db, obj_in=user_in)
    # create email confirmation token
    token = token_urlsafe()
    token_in_db = crud.user.create_confirmation_token(
        db,
        obj_in=schemas.ConfirmationTokenCreate(
            token=security.get_token_hash(token, salt="confirm")
        ),
        user_id=user.id,
    )
    if token_in_db:
        mail.send_email_confirmation(
            background_tasks=background_tasks,
            first_name=user.first_name,
            email=user.email,
            confirmation_token=token,
        )

    return user


@router.get("", response_model=list[schemas.User])
def read_users(
    q: str = Query(Annotated[str | None, Query(max_length=50)]),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve list of all users or a list of users filtered by a search query."""
    users = crud.user.get_multi_by_query(db, q=q, skip=skip, limit=limit)
    return users


@router.put("/{user_id}", response_model=schemas.User)
def update_current_user(
    user_id: UUID,
    password: str = Body(None),
    first_name: str = Body(None),
    last_name: str = Body(None),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update user by id."""
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Permission denied"
        )
    user_in = schemas.UserUpdate(**user.__dict__)
    if password is not None:
        user_in.password = password
    if first_name is not None:
        user_in.first_name = first_name
    if last_name is not None:
        user_in.last_name = last_name
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.get("/current", response_model=schemas.User)
def read_current_user(
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve current user."""
    return current_user
