from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.team import create_random_team
from app.tests.utils.team_member import create_random_team_member
from app.tests.utils.user import create_random_user


def test_create_team_member(db: Session) -> None:
    """Verify a new team member can be added to an existing team."""
    team_owner = create_random_user(db)
    team = create_random_team(db, owner_id=team_owner.id)
    user = create_random_user(db)
    team_member = create_random_team_member(db, member_id=user.id, team_id=team.id)
    assert team_member
    assert user.id == team_member.member_id
    assert team.id == team_member.team_id


def test_get_list_of_team_members(db: Session) -> None:
    """Verify a team id can return a list of team members."""
    team = create_random_team(db)
    member1 = create_random_team_member(db, team_id=team.id)
    member2 = create_random_team_member(db, team_id=team.id)
    team_members = crud.team_member.get_list_of_team_members(db, team_id=team.id)
    assert type(team_members) is list
    assert len(team_members) == 3  # owner + two added team members
    for team_member in team_members:
        assert (
            team.owner_id == team_member.member_id
            or member1.member_id == team_member.member_id
            or member2.member_id == team_member.member_id
        )
