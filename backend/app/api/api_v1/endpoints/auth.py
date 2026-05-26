import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    Form,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi import Cookie
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps, mail
from app.core import security
from app.core.config import settings
from app.core.limiter import limiter


router = APIRouter()

logger = logging.getLogger("__name__")


@router.post("/access-token")
@limiter.limit("10/minute;100/hour")
def login_access_token(
    request: Request,
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

    # Update login and activity timestamps
    crud.user.update_last_login(db, user=user)

    access_token = security.create_access_token(user.id)
    refresh_token = security.create_refresh_token(db, user.id)

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
    if not refresh_token or not refresh_token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing or malformed",
        )

    # Remove "Bearer " prefix and strip whitespace
    token = refresh_token.removeprefix("Bearer ").strip()

    # Validate token and get payload
    payload = security.validate_token_and_get_payload(token, "refresh")

    # Require a jti claim in the payload
    jti_str = payload.get("jti")
    if not jti_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token payload missing jti",
        )
    jti = UUID(jti_str)

    # Check if token is revoked
    db_token = crud.refresh_token.get_by_jti(db, jti=jti)
    if (
        not db_token
        or db_token.revoked
        or db_token.expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired",
        )

    # Revoke the old refresh token
    crud.refresh_token.revoke(db, jti=jti)

    # Get user from payload
    user = security.get_user_from_token_payload(db, payload)

    # Issue new access token
    new_access_token = security.create_access_token(user.id)
    new_refresh_token = security.create_refresh_token(db, user.id)

    # Set authentication cookies
    security.set_auth_cookies(response, new_access_token, new_refresh_token)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
    }


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
@limiter.limit("5/hour")
def request_new_email_confirmation_link(
    request: Request,
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


@router.post("/change-email", status_code=status.HTTP_200_OK)
def request_email_change(
    current_password: Annotated[str, Form()],
    new_email: Annotated[EmailStr, Form()],
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_approved_user),
) -> Any:
    """Request an email address change. Requires password re-authentication."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo accounts cannot change email",
        )
    # Re-authenticate
    user = crud.user.authenticate(
        db, email=current_user.email, password=current_password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided current password is incorrect",
        )
    # Reject if new email matches current email
    if new_email.lower() == user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New email must be different from current email",
        )
    # Check new email is not already in use
    existing = crud.user.get_by_email(db, email=new_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already in use",
        )
    # Clean up any existing email-change tokens for this user
    crud.user.remove_single_use_tokens_by_salt(db, user_id=user.id, salt="emailchg")
    # Set pending email
    crud.user.update(
        db, db_obj=user, obj_in=schemas.UserUpdate(pending_email=new_email)
    )
    if settings.MAIL_ENABLED:
        # Create verification token
        token = secrets.token_urlsafe()
        crud.user.create_single_use_token(
            db,
            obj_in=schemas.SingleUseTokenCreate(
                token=security.get_token_hash(token, salt="emailchg")
            ),
            user_id=user.id,
        )
        # Send verification email to new address
        mail.send_email_change_verification(
            background_tasks=background_tasks,
            first_name=user.first_name,
            new_email=new_email,
            verification_token=token,
        )
        # Send informational notification to old address
        mail.send_email_change_notification(
            background_tasks=background_tasks,
            first_name=user.first_name,
            old_email=user.email,
        )
        logger.info(
            "Email change requested for user %s from %s to %s",
            user.id,
            user.email,
            new_email,
        )
        return {"detail": "verification_sent"}
    else:
        # Mail disabled — apply change immediately
        crud.user.update(
            db, db_obj=user, obj_in={"email": new_email, "pending_email": None}
        )
        logger.info(
            "Email change applied immediately (mail disabled) for user %s to %s",
            user.id,
            new_email,
        )
        return {"detail": "email_changed"}


@router.get(
    "/confirm-email-change",
    response_class=RedirectResponse,
    status_code=status.HTTP_302_FOUND,
)
def confirm_email_change(token: str, db: Session = Depends(deps.get_db)) -> Any:
    """Confirm email change by verifying the token sent to the new email address."""
    token_db_obj = crud.user.get_single_use_token(
        db, token_hash=security.get_token_hash(token, salt="emailchg")
    )
    if not token_db_obj:
        return settings.API_DOMAIN + "/auth/login?error=invalid"
    if security.check_token_expired(token_db_obj):
        crud.user.remove_single_use_token(db, db_obj=token_db_obj)
        return settings.API_DOMAIN + "/auth/login?error=expired"
    # Find user associated with token
    user = crud.user.get(db, id=token_db_obj.user_id)
    if not user or not user.pending_email:
        crud.user.remove_single_use_token(db, db_obj=token_db_obj)
        return settings.API_DOMAIN + "/auth/login?error=invalid"
    # Re-check uniqueness (TOCTOU guard)
    existing = crud.user.get_by_email(db, email=user.pending_email)
    if existing:
        crud.user.remove_single_use_token(db, db_obj=token_db_obj)
        return settings.API_DOMAIN + "/auth/login?error=email_taken"
    # Apply the email change
    new_email = user.pending_email
    try:
        crud.user.update(
            db, db_obj=user, obj_in={"email": new_email, "pending_email": None}
        )
    except IntegrityError:
        return settings.API_DOMAIN + "/auth/login?error=email_taken"
    # Remove token
    crud.user.remove_single_use_token(db, db_obj=token_db_obj)
    logger.info("Email change completed for user %s to %s", user.id, new_email)
    return settings.API_DOMAIN + "/auth/login?email_changed=true"


@router.get("/reset-password")
@limiter.limit("5/hour")
def send_reset_password_by_email(
    request: Request,
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
@limiter.limit("10/hour")
def approve_user_account(
    request: Request,
    token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
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
@limiter.limit("10/hour")
def reset_user_password(
    request: Request,
    password: str = Body(),
    token: str = Body(),
    db: Session = Depends(deps.get_db),
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
