from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models.enums.api_key_scope import MAX_ACTIVE_API_KEYS

router = APIRouter()


def verify_not_demo_user(current_user: models.User) -> None:
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo accounts cannot manage API keys",
        )


@router.get("", response_model=List[schemas.APIKey])
def read_api_keys(
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Returns current user's active api keys."""
    verify_not_demo_user(current_user)
    return crud.api_key.get_multi_by_user(db, user_id=current_user.id)


@router.post("", response_model=schemas.APIKey, status_code=status.HTTP_201_CREATED)
def create_api_key(
    api_key_in: schemas.APIKeyRequest,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Creates new api key with requested name and scopes for current user."""
    verify_not_demo_user(current_user)
    if crud.api_key.count_active_by_user(db, user_id=current_user.id) >= (
        MAX_ACTIVE_API_KEYS
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {MAX_ACTIVE_API_KEYS} active API keys reached",
        )
    return crud.api_key.create_with_user(
        db,
        user_id=current_user.id,
        scopes=api_key_in.scopes,
        name=api_key_in.name,
    )


@router.patch("/{api_key_id}", response_model=schemas.APIKey)
def update_api_key(
    api_key_id: UUID,
    api_key_in: schemas.APIKeyUpdateRequest,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Updates name and/or scopes of current user's api key."""
    verify_not_demo_user(current_user)
    api_key = crud.api_key.update_by_user(
        db, api_key_id=api_key_id, user_id=current_user.id, obj_in=api_key_in
    )
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )
    return api_key


@router.delete("/{api_key_id}", response_model=schemas.APIKey)
def revoke_api_key(
    api_key_id: UUID,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Deactivates current user's api key."""
    verify_not_demo_user(current_user)
    api_key = crud.api_key.deactivate(
        db, api_key_id=api_key_id, user_id=current_user.id
    )
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )
    return api_key
