import os
import shutil
from secrets import token_urlsafe
from typing import Annotated, Any
from uuid import uuid4, UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Request,
    status,
    UploadFile,
    Query,
)
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps, mail
from app.core.config import settings
from app.core import security
from app.models.utils.user import validate_password

router = APIRouter()


@router.post("", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    password: str = Body(title="Password", min_length=12, max_length=128),
    email: EmailStr = Body(title="Email", max_length=254),
    first_name: str = Body(title="First name", min_length=2, max_length=64),
    last_name: str = Body(title="Last name", min_length=2, max_length=64),
) -> Any:
    """Create new user with unique email."""
    existing_user = crud.user.get_by_email(db, email=email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email address already in use"
        )
    # verify password meets minimum requirements
    validate_password(password)
    user_in = schemas.UserCreate(
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name,
    )
    user = crud.user.create(db, obj_in=user_in)
    if settings.MAIL_ENABLED:
        # create email confirmation token
        confirmation_token = token_urlsafe()
        approve_token = token_urlsafe()
        confirmation_token_in_db = crud.user.create_single_use_token(
            db,
            obj_in=schemas.SingleUseTokenCreate(
                token=security.get_token_hash(confirmation_token, salt="confirm")
            ),
            user_id=user.id,
        )
        approve_token_in_db = crud.user.create_single_use_token(
            db,
            obj_in=schemas.SingleUseTokenCreate(
                token=security.get_token_hash(approve_token, salt="approve")
            ),
            user_id=user.id,
        )
        if confirmation_token_in_db and approve_token_in_db:
            mail.send_email_confirmation(
                background_tasks=background_tasks,
                first_name=user.first_name,
                email=user.email,
                confirmation_token=confirmation_token,
            )
            mail.send_admins_new_registree_notification(
                background_tasks=background_tasks,
                first_name=user.first_name,
                email=user.email,
                approve_token=approve_token,
            )
    else:
        # mail disabled - enable account without email / admin confirmation
        crud.user.update(
            db,
            db_obj=user,
            obj_in=schemas.UserUpdate(is_approved=True, is_email_confirmed=True),
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


@router.post("/profile", status_code=status.HTTP_200_OK)
def upload_user_profile(
    request: Request,
    files: UploadFile,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    if request.client and request.client.host == "testclient":
        upload_dir = f"{settings.TEST_STATIC_DIR}/users/{current_user.id}"
    else:
        upload_dir = f"{settings.STATIC_DIR}/users/{current_user.id}"
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    os.makedirs(upload_dir)

    if files.content_type == "image/jpeg":
        out_path = os.path.join(upload_dir, str(uuid4()) + ".jpg")
    elif files.content_type == "image/png":
        out_path = os.path.join(upload_dir, str(uuid4()) + ".png")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Must be png or jpeg format"
        )

    with open(out_path, "wb") as buffer:
        shutil.copyfileobj(files.file, buffer)

    return {"upload-status": "success"}


@router.delete("/profile", status_code=status.HTTP_202_ACCEPTED)
def delete_user_profile(
    request: Request,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    if request.client and request.client.host == "testclient":
        upload_dir = f"{settings.TEST_STATIC_DIR}/users/{current_user.id}"
    else:
        upload_dir = f"{settings.STATIC_DIR}/users/{current_user.id}"
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
