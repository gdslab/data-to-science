from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.team_member import TeamMemberCreate
from app.tests.utils.team import create_random_team
from app.tests.utils.user import create_random_user


def create_random_team_member(
    db: Session,
    member_id: UUID | None = None,
    team_id: UUID | None = None,
) -> models.TeamMember:
    if member_id is None:
        user = create_random_user(db=db)
        member_id = user.id
    if team_id is None:
        team = create_random_team(db=db)
        team_id = team.id
    team_member_in = TeamMemberCreate()
    return crud.team_member.create_with_team(
        db=db, obj_in=team_member_in, member_id=member_id, team_id=team_id
    )
