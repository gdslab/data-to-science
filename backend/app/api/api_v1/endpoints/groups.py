from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import Required
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post("/", response_model=schemas.Group)
def create_group(
    group_in: schemas.GroupCreate,
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Create new group for current user."""
    # create group in database
    group = crud.group.create_with_owner(db=db, obj_in=group_in, owner_id=current_user.id)
    return group


@router.get("/", response_model=list[schemas.Group])
def read_groups(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve list of groups owned by current user."""
    groups = crud.group.get_multi_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return groups
