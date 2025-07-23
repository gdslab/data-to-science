import logging
import os
import secrets
from typing import Any, Annotated, Literal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    Form,
    HTTPException,
    Response,
    status,
)
from fastapi import Cookie
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps, mail
from app.core import security
from app.core.config import settings


router = APIRouter()

logger = logging.getLogger("__name__")


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
    refresh_token = security.create_refresh_token(user.id)

    # Set authentication cookies
    security.set_auth_cookies(response, access_token, refresh_token)

    return status.HTTP_200_OK


@router.post("/refresh-token")
def refresh_access_token(
    response: Response,
    refresh_token: str = Cookie(None),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Refresh access token using refresh token."""
    # Check if refresh token is provided
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found"
        )
    # Check if refresh token starts with "Bearer "
    if not refresh_token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    # Remove "Bearer " prefix and strip whitespace
    token = refresh_token.removeprefix("Bearer ").strip()

    # Validate token and get payload
    payload = security.validate_token_and_get_payload(token, "refresh")

    # Get user from payload
    user = security.get_user_from_token_payload(db, payload)

    # Issue new access token
    new_access_token = security.create_access_token(user.id)
    new_refresh_token = security.create_refresh_token(user.id)

    # Set authentication cookies
    security.set_auth_cookies(response, new_access_token, new_refresh_token)

    return {"msg": "Access token refreshed"}


@router.get("/remove-access-token")
def logout_access_token(response: Response) -> Any:
    """Remove cookie containing JWT access token."""
    response.delete_cookie(key="access_token")
    return status.HTTP_200_OK


@router.post("/test-token", response_model=schemas.user.User)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """Test access token."""
    return current_user


@router.get(
    "/confirm-email", response_class=RedirectResponse, status_code=status.HTTP_302_FOUND
)
def confirm_user_email_address(token: str, db: Session = Depends(deps.get_db)) -> Any:
    """Confirm email address for user account."""
    token_db_obj = crud.user.get_single_use_token(
        db, token_hash=security.get_token_hash(token, salt="confirm")
    )
    # check if token is valid
    if not token_db_obj:
        return settings.API_DOMAIN + "/auth/login?error=invalid"
    if security.check_token_expired(token_db_obj):
        crud.user.remove_single_use_token(db, db_obj=token_db_obj)
        return settings.API_DOMAIN + "/auth/login?error=expired"
    # find user associated with token
    user = crud.user.get(db, id=token_db_obj.user_id)
    if not user:
        crud.user.remove_single_use_token(db, db_obj=token_db_obj)
        return settings.API_DOMAIN + "/auth/login?error=notfound"
    # update user's email confirmation status
    user_update_in = schemas.user.UserUpdate(is_email_confirmed=True)
    user_updated = crud.user.update(db, db_obj=user, obj_in=user_update_in)
    if not user_updated or not user_updated.is_email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to confirm email"
        )
    # remove token from database
    crud.user.remove_single_use_token(db, db_obj=token_db_obj)
    # redirect to login page
    return settings.API_DOMAIN + "/auth/login?email_confirmed=true"


@router.get("/request-email-confirmation", status_code=status.HTTP_200_OK)
def request_new_email_confirmation_link(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
) -> Any:
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
    token_in_db = crud.user.create_single_use_token(
        db,
        obj_in=schemas.single_use_token.SingleUseTokenCreate(
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


@router.post("/change-password", response_model=schemas.user.User)
def change_password(
    current_password: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_approved_user),
) -> Any:
    """Update user password when provided with current password and new password."""
    user = crud.user.authenticate(
        db, email=current_user.email, password=current_password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided current password is incorrect",
        )
    if user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo accounts cannot change password",
        )
    user_in = schemas.user.UserUpdate(password=new_password)
    user_updated = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user_updated


@router.get("/reset-password")
def send_reset_password_by_email(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
) -> Any:
    # check if user with provided email exists
    user = crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_200_OK)
    first_name, email = user.first_name, user.email
    # create new token
    token = secrets.token_urlsafe()
    token_in_db = crud.user.create_single_use_token(
        db,
        obj_in=schemas.SingleUseTokenCreate(
            token=security.get_token_hash(token, salt="reset")
        ),
        user_id=user.id,
    )
    if token_in_db:
        mail.send_password_recovery(
            background_tasks=background_tasks,
            first_name=first_name,
            email=email,
            recovery_token=token,
        )


@router.get("/approve-account")
def approve_user_account(
    token: str, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)
) -> Any:
    token_db_obj = crud.user.get_single_use_token(
        db, token_hash=security.get_token_hash(token, salt="approve")
    )
    # check if token is valid
    if not token_db_obj:
        return {"status": "token invalid"}
    if security.check_token_expired(token_db_obj, minutes=1440):
        crud.user.remove_single_use_token(db, db_obj=token_db_obj)
        return {"status": "token expired"}
    # find user associated with token
    user = crud.user.get(db, id=token_db_obj.user_id)
    if not user:
        crud.user.remove_single_use_token(db, db_obj=token_db_obj)
        return {"status": "account not found"}
    # update user's email confirmation status
    user_update_in = schemas.user.UserUpdate(is_approved=True)
    user_updated = crud.user.update(db, db_obj=user, obj_in=user_update_in)
    if not user_updated or not user_updated.is_approved:
        return {"status": "unable to approve"}
    # remove token from database
    crud.user.remove_single_use_token(db, db_obj=token_db_obj)
    # email user
    mail.send_account_approved(
        background_tasks=background_tasks,
        first_name=user.first_name,
        email=user.email,
        confirmed=user.is_email_confirmed,
    )
    # redirect to login page
    return {"status": "approved"}


@router.post("/reset-password")
def reset_user_password(
    password: str = Body(), token: str = Body(), db: Session = Depends(deps.get_db)
) -> Any:
    """Change password for user account."""
    token_db_obj = crud.user.get_single_use_token(
        db, token_hash=security.get_token_hash(token, salt="reset")
    )
    # check if token is valid
    if not token_db_obj:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reset token no longer active",
        )
    if security.check_token_expired(token_db_obj):
        # remove token from database
        crud.user.remove_single_use_token(db, db_obj=token_db_obj)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Reset token has expired"
        )
    # find user associated with token
    user = crud.user.get(db, id=token_db_obj.user_id)
    if not user:
        # remove token from database
        crud.user.remove_single_use_token(db, db_obj=token_db_obj)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    # update user's email confirmation status
    user_update_in = schemas.user.UserUpdate(password=password)
    user_updated = crud.user.update(db, db_obj=user, obj_in=user_update_in)
    if not user_updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to confirm email"
        )
    # remove token from database
    crud.user.remove_single_use_token(db, db_obj=token_db_obj)
    # redirect to login page
    return {"status": "success"}


@router.get("/request-api-key", status_code=status.HTTP_200_OK)
def get_api_key(
    response: Response,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Returns user obj with api key."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo user cannot request api key",
        )
    api_key = crud.api_key.create_with_user(db, user_id=current_user.id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create API key",
        )


@router.get("/revoke-api-key", status_code=status.HTTP_200_OK)
def deactivate_api_key(
    response: Response,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Deactivates user's api key."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo accounts cannot create teams",
        )
    api_key = crud.api_key.deactivate(db, user_id=current_user.id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    if api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to revoke API key",
        )
