from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security


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
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials"
        )
    elif not crud.user.is_approved(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Account needs approval"
        )
    access_token = security.create_access_token(user.id)
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )
    return status.HTTP_200_OK


@router.post("/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """Test access token."""
    return current_user
