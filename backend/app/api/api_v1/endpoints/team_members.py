from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.post("", response_model=schemas.TeamMember, status_code=status.HTTP_201_CREATED)
def create_team_member(
    team_id: UUID,
    team_member_in: schemas.TeamMemberCreate,
    team: models.Team = Depends(deps.can_read_write_delete_team),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new team member."""
    already_on_team = crud.team_member.get_team_member_by_email(
        db, email=team_member_in.email, team_id=team_id
    )
    if already_on_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Already on team"
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


@router.post(
    "/multi",
    response_model=list[schemas.TeamMember],
    status_code=status.HTTP_201_CREATED,
)
def create_team_members(
    team_id: UUID,
    team_members: list[UUID],
    team: models.Team = Depends(deps.can_read_write_delete_team),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create multiple new team members."""
    team_members = crud.team_member.create_multi_with_team(
        db, team_members=team_members, team_id=team.id
    )
    return team_members


@router.get("", response_model=list[schemas.TeamMember])
def read_team_members(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    team: models.Team = Depends(deps.can_read_team),
) -> Any:
    """Retrieve list of team members."""
    team_members = crud.team_member.get_list_of_team_members(
        db, team_id=team.id, skip=skip, limit=limit
    )
    return team_members


@router.delete(
    "/{member_id}",
    response_model=schemas.TeamMember,
    status_code=status.HTTP_200_OK,
)
def remove_team_member(
    team_id: UUID,
    member_id: UUID,
    team: models.Team = Depends(deps.can_read_write_delete_team),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Remove team member."""
    if team.owner_id == member_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove self (owner) from team",
        )
    removed_team_member = crud.team_member.remove(db, id=member_id)
    return removed_team_member
