from sqlalchemy.orm import Session

from app import crud
from app.schemas.team import TeamUpdate
from app.tests.utils.project import create_project
from app.tests.utils.team import create_team
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user
from app.tests.utils.utils import random_team_description, random_team_name


def test_create_team(db: Session) -> None:
    title = random_team_name()
    description = random_team_description()
    user = create_user(db)
    team = create_team(db, title=title, description=description, owner_id=user.id)
    assert team.title == title
    assert team.description == description
    assert team.owner_id == user.id


def test_get_team(db: Session) -> None:
    team = create_team(db)
    stored_team = crud.team.get(db, id=team.id)
    assert stored_team
    assert team.id == stored_team.id
    assert team.title == stored_team.title
    assert team.description == stored_team.description
    assert team.owner_id == stored_team.owner_id


def test_get_teams_by_member(db: Session) -> None:
    user = create_user(db)
    team1 = create_team(db)
    team2 = create_team(db)
    create_team(db)  # user not member of this team
    create_team_member(db, email=user.email, team_id=team1.id)
    create_team_member(db, email=user.email, team_id=team2.id)
    teams = crud.team.get_user_team_list(db, user_id=user.id)
    assert type(teams) is list
    assert len(teams) == 2
    for team in teams:
        assert team1.id == team.id or team2.id == team.id


def test_update_team(db: Session) -> None:
    team = create_team(db)
    new_description = random_team_description()
    team_in_update = TeamUpdate(description=new_description)
    team_update = crud.team.update(db, db_obj=team, obj_in=team_in_update)
    assert team.id == team_update.id
    assert team.title == team_update.title
    assert new_description == team_update.description
    assert team.owner_id == team_update.owner_id


def test_delete_team(db: Session) -> None:
    user = create_user(db)
    team = create_team(db, owner_id=user.id)
    team2 = crud.team.remove(db, id=team.id)
    team3 = crud.team.get(db, id=team.id)
    assert team3 is None
    assert team2
    assert team2.id == team.id
    assert team2.title == team.title
    assert team2.description == team.description
    assert team2.owner_id == user.id


def test_delete_team_with_project_association(db: Session) -> None:
    user = create_user(db)
    team = create_team(db, owner_id=user.id)
    project = create_project(db, owner_id=user.id, team_id=team.id)
    crud.team.remove(db, id=team.id)
    team2 = crud.team.get(db, id=team.id)
    project2 = crud.project.get(db, id=project.id)
    assert team2 is None
    assert project.team_id == team.id
    assert project2
    assert project2.team_id is None
