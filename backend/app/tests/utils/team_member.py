from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.team_member import TeamMemberCreate
from app.schemas.role import Role
from app.tests.utils.team import create_team
from app.tests.utils.user import create_user


def create_team_member(
    db: Session,
    email: Optional[str] = None,
    team_id: Optional[UUID] = None,
    role: Optional[Role] = None,
) -> models.TeamMember:
    if email is None:
        user = create_user(db)
        email = user.email
    if team_id is None:
        team = create_team(db)
        team_id = team.id
    if role is None:
        role = Role.VIEWER
    team_member_in = TeamMemberCreate(email=email, role=role)
    team_member = crud.team_member.create_with_team(
        db, obj_in=team_member_in, team_id=team_id
    )
    if not team_member:
        raise Exception("Team member not created")
    return team_member
