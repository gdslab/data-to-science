from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import Required
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post("/", response_model=schemas.Team, status_code=status.HTTP_201_CREATED)
def create_team(
    team_in: schemas.TeamCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
):
    """Create new team for current user."""
    team = crud.team.create_with_owner(db=db, obj_in=team_in, owner_id=current_user.id)
    return team


@router.get("/", response_model=list[schemas.Team])
def read_teams(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve list of teams owned by current user."""
    teams = crud.team.get_multi_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return teams


@router.get("/{team_id}", response_model=schemas.Team)
def read_team(
    team_id: str,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """Retrieve team owned by current user."""
    team = crud.team.get(db=db, id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if team.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Permission denied")
    return team


@router.put("/{team_id}", response_model=schemas.Team)
def update_team(
    team_id: str,
    team_in: schemas.TeamUpdate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update a team owned by current user."""
    team = crud.team.get(db=db, id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if team.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Permission denied")
    team = crud.team.update(db=db, db_obj=team, obj_in=team_in)
    return team

@router.delete("/{team_id}", response_model=schemas.Team)
def delete_team(
    team_id: str,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Delete a team owned by current user."""
    team = crud.team.get(db=db, id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if team.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Permission denied")
    team = crud.team.remove(db=db, id=team_id)
    return team
