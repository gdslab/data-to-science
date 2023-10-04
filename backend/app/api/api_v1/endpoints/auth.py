from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
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
    elif not crud.user.is_approved(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Account awaiting approval"
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


@router.get("/confirm-email", response_class=RedirectResponse, status_code=302)
def confirm_user_email_address(token: str, db: Session = Depends(deps.get_db)):
    """Confirm email address for user account."""
    token_data = deps.decode_jwt(token)
    if token_data.sub:
        user = crud.user.get(db, id=token_data.sub)
    else:
        user = None
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    user_update_in = schemas.UserUpdate(is_email_confirmed=True)
    user_updated = crud.user.update(db, db_obj=user, obj_in=user_update_in)
    if not user_updated or not user_updated.is_email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to confirm email"
        )
    return settings.DOMAIN + "/auth/login?email_confirmed=true"
