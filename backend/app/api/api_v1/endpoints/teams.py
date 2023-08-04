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
    """Create new team for current user."""
    team = crud.team.create_with_owner(db, obj_in=team_in, owner_id=current_user.id)
    return team


@router.get("", response_model=list[schemas.Team])
def read_teams(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve list of teams current user belongs to."""
    teams = crud.team.get_user_team_list(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return teams


@router.get("/{team_id}", response_model=schemas.Team)
def read_team(
    team_id: UUID,
    db: Session = Depends(deps.get_db),
    team: models.Team = Depends(deps.can_read_team),
) -> Any:
    """Retrieve team if current user has access to it."""
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    return team


@router.get("/{team_id}/members", response_model=list[schemas.TeamMember])
def read_team_members(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    team: models.Team = Depends(deps.can_read_team),
) -> Any:
    """Retrieve members of a team."""
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found."
        )
    team_members = crud.team_member.get_list_of_team_members(
        db, team_id=team.id, skip=skip, limit=limit
    )
    return team_members


@router.put("/{team_id}", response_model=schemas.Team)
def update_team(
    team_id: UUID,
    team_in: schemas.TeamUpdate,
    team: models.Team = Depends(deps.can_read_write_team),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update team if current user is team owner or member."""
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    team = crud.team.update(db, db_obj=team, obj_in=team_in)
    return team


@router.post(
    "/{team_id}/members",
    response_model=schemas.TeamMember,
    status_code=status.HTTP_201_CREATED,
)
def create_team_member(
    team_id: UUID,
    team_member_in: schemas.TeamMemberCreate,
    team: models.Team = Depends(deps.can_read_write_team),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Add team member to team if current user is team owner."""
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    team_member = crud.team_member.create_with_team(
        db, obj_in=team_member_in, team_id=team.id
    )
    if not team_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find user with provided email address",
        )
    return team_member
