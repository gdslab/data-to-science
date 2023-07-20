from sqlalchemy.orm import Session

from app.tests.utils.team import create_random_team
from app.tests.utils.team_member import create_random_team_member
from app.tests.utils.user import create_random_user


def test_create_standard_team_member(db: Session) -> None:
    """Verify a new standard team member can be added to an existing team."""
    team_owner = create_random_user(db=db)
    team = create_random_team(db=db, owner_id=team_owner.id)
    user = create_random_user(db=db)
    team_member = create_random_team_member(db=db, member_id=user.id, team_id=team.id)
    assert team_member
    assert user.id == team_member.member_id
    assert team.id == team_member.team_id


def test_create_manager_team_member(db: Session) -> None:
    """Verify a new manager team member can be added to an existing team."""
    team_owner = create_random_user(db=db)
    team = create_random_team(db=db, owner_id=team_owner.id)
    user = create_random_user(db=db)
    team_member = create_random_team_member(db=db, member_id=user.id, team_id=team.id)
    assert team_member
    assert user.id == team_member.member_id
    assert team.id == team_member.team_id
