from sqlalchemy.orm import Session

from app import crud
from app.schemas.team import TeamCreate, TeamUpdate
from app.tests.utils.team import create_random_team
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_team_description, random_team_name


def test_create_team(db: Session) -> None:
    """Test creating a new team."""
    # team attributes
    title = random_team_name()
    description = random_team_description()
    # team owner
    user = create_random_user(db)
    # create team
    team = create_random_team(
        db, title=title, description=description, owner_id=user.id
    )

    assert team.title == title
    assert team.description == description
    assert team.owner_id == user.id


def test_get_team(db: Session) -> None:
    """Test retrieving a team by id."""
    # create team
    team = create_random_team(db)
    # use team id to retrieve team
    stored_team = crud.team.get(db=db, id=team.id)

    assert stored_team
    assert team.id == stored_team.id
    assert team.title == stored_team.title
    assert team.description == stored_team.description
    assert team.owner_id == stored_team.owner_id


def test_update_team(db: Session) -> None:
    """Test updating an existing team."""
    # create team
    team = create_random_team(db)
    # generate new values for fields to be updated
    new_description = random_team_description()
    # update the team
    team_in_update = TeamUpdate(description=new_description)
    team_update = crud.team.update(db=db, db_obj=team, obj_in=team_in_update)

    assert team.id == team_update.id
    assert team.title == team_update.title
    assert new_description == team_update.description
    assert team.owner_id == team_update.owner_id


def test_delete_team(db: Session) -> None:
    """Test removing an existing team."""
    # create team
    team = create_random_team(db)
    # remove team
    team_removed = crud.team.remove(db=db, id=team.id)
    # attempt to retrieve removed team
    team_after_remove = crud.team.get(db=db, id=team.id)

    assert team_after_remove is None
    assert team_removed.id == team.id
    assert team_removed.title == team.title
    assert team_removed.description == team.description
    assert team_removed.owner_id == team.owner_id
