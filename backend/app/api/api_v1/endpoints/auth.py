import secrets
from typing import Any, Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Response,
    status,
)
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps, mail
from app.core import security
from app.core.config import settings


router = APIRouter()


@router.post("/access-token")
def login_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(deps.get_db),
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests."""
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if not crud.user.is_email_confirmed(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account requires email confirmation",
        )
    if not crud.user.is_approved(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account requires approval"
        )
    access_token = security.create_access_token(user.id)
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )
    return status.HTTP_200_OK


@router.get("/remove-access-token")
def logout_access_token(response: Response) -> Any:
    """Remove cookie containing JWT access token."""
    response.delete_cookie(key="access_token")
    return status.HTTP_200_OK


@router.post("/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """Test access token."""
    return current_user


@router.get(
    "/confirm-email", response_class=RedirectResponse, status_code=status.HTTP_302_FOUND
)
def confirm_user_email_address(token: str, db: Session = Depends(deps.get_db)):
    """Confirm email address for user account."""
    token_db_obj = crud.user.get_confirmation_token(
        db, token_hash=security.get_token_hash(token, salt="confirm")
    )
    # check if token is valid
    if not token_db_obj:
        return settings.DOMAIN + "/auth/login?error=invalid"
    if security.check_token_expired(token_db_obj):
        return settings.DOMAIN + "/auth/login?error=expired"
    # find user associated with token
    user = crud.user.get(db, id=token_db_obj.user_id)
    if not user:
        return settings.DOMAIN + "/auth/login?error=notfound"
    # update user's email confirmation status
    user_update_in = schemas.UserUpdate(is_email_confirmed=True)
    user_updated = crud.user.update(db, db_obj=user, obj_in=user_update_in)
    if not user_updated or not user_updated.is_email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to confirm email"
        )
    # remove token from database
    crud.user.remove_confirmation_token(db, db_obj=token_db_obj)
    # redirect to login page
    return settings.DOMAIN + "/auth/login?email_confirmed=true"


@router.get("/request-email-confirmation", status_code=status.HTTP_200_OK)
def request_new_email_confirmation_link(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
):
    """Send a new email confirmation link to the provided email address."""
    # find user requesting a new token
    user = crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    first_name, email = user.first_name, user.email
    # create new token
    token = secrets.token_urlsafe()
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
            first_name=first_name,
            email=email,
            confirmation_token=token,
        )


@router.post("/change-password")
def change_password(
    current_password: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_approved_user),
):
    """Update user password when provided with current password and new password."""
    user = crud.user.authenticate(
        db, email=current_user.email, password=current_password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided current password is incorrect",
        )
    user_in = schemas.UserUpdate(password=new_password)
    user_updated = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user_updated
