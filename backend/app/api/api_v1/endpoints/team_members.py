from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.schemas.role import Role


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
    if team_member_in.email:
        already_on_team = crud.team_member.get_team_member_by_email(
            db, email=str(team_member_in.email), team_id=team_id
        )
    elif team_member_in.member_id:
        already_on_team = crud.team_member.get_team_member_by_id(
            db, user_id=team_member_in.member_id, team_id=team_id
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or member_id must be provided",
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
    team_members_in_db = crud.team_member.create_multi_with_team(
        db, team_members=team_members, team_id=team.id
    )
    return team_members_in_db


@router.get("", response_model=list[schemas.TeamMember])
def read_team_members(
    db: Session = Depends(deps.get_db),
    team: models.Team = Depends(deps.can_read_team),
) -> Any:
    """Retrieve list of team members."""
    team_members = crud.team_member.get_list_of_team_members(db, team_id=team.id)

    return team_members


@router.put(
    "/{team_member_id}",
    response_model=schemas.TeamMember,
    status_code=status.HTTP_200_OK,
)
def update_team_member(
    team_member_id: UUID,
    team_member_in: schemas.TeamMemberUpdate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
    team: models.Team = Depends(deps.can_read_write_team),
) -> Any:
    """Update team member role."""
    current_user_team_member = crud.team_member.get_team_member_by_id(
        db, user_id=current_user.id, team_id=team.id
    )
    team_member_to_be_updated = crud.team_member.get(db, id=team_member_id)
    if team_member_to_be_updated is None or current_user_team_member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found"
        )
    if team_member_to_be_updated.team_id != team.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found"
        )

    # Check if MANAGER is trying to modify OWNER or promote to OWNER
    if current_user_team_member.role == Role.MANAGER:
        if (
            team_member_to_be_updated.role == Role.OWNER
            or team_member_in.role == Role.OWNER
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot modify owner roles or promote to owner",
            )

    # Check if current user is trying to modify the team creator
    if team_member_to_be_updated.member_id == team.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team creator cannot be modified",
        )

    updated_team_member = crud.team_member.update_team_member(
        db, team_member_in=team_member_in, team_member_id=team_member_id
    )
    if not updated_team_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found"
        )

    return updated_team_member


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
    team_member = crud.team_member.get(db, id=member_id)
    if team_member:
        if team.owner_id == team_member.member_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove team creator",
            )
        removed_team_member = crud.team_member.remove_team_member(
            db, member_id=team_member.member_id, team_id=team.id
        )
        return removed_team_member
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found"
        )
