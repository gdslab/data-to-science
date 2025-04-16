from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post("", response_model=schemas.Team, status_code=status.HTTP_201_CREATED)
def create_team(
    team_in: schemas.TeamCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new team."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo accounts cannot create teams",
        )

    try:
        team = crud.team.create_with_owner(db, obj_in=team_in, owner_id=current_user.id)
    except ValueError as e:
        if str(e) == "Project not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        elif str(e) == "User is not an owner of the project":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Must be an owner of the project to create a team",
            )
        elif str(e) == "Project already has a team":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project already has a team",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to create team"
            )
    if not team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to create team"
        )

    return team


@router.get("/{team_id}", response_model=schemas.Team)
def read_team(
    team_id: UUID,
    db: Session = Depends(deps.get_db),
    team: models.Team = Depends(deps.can_read_team),
) -> Any:
    """Retrieve existing team."""
    return team


@router.get("", response_model=list[schemas.Team])
def read_teams(
    owner_only: bool = False,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve list of user's teams."""
    teams = crud.team.get_user_team_list(
        db, user_id=current_user.id, owner_only=owner_only
    )
    return teams


@router.put("/{team_id}", response_model=schemas.Team)
def update_team(
    team_id: UUID,
    team_in: schemas.TeamUpdate,
    team: models.Team = Depends(deps.can_read_write_delete_team),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update existing team."""
    updated_team = crud.team.update_team(
        db, team_in=team_in, team_id=team_id, user_id=current_user.id
    )
    if not updated_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to update team"
        )
    return updated_team


@router.delete("/{team_id}", response_model=schemas.Team)
def delete_team(
    team_id: UUID,
    team: models.Team = Depends(deps.can_read_write_delete_team),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Remove existing team."""
    removed_team = crud.team.delete_team(db=db, team_id=team_id)
    return removed_team
