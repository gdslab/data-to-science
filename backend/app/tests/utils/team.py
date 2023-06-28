from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.team import TeamCreate
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_team_name, random_team_description


def create_random_team(
    db: Session,
    *, 
    title: str | None = None,
    description: str | None = None,
    owner_id: UUID | None = None
) -> models.Team:
    if owner_id is None:
        user = create_random_user(db)
        owner_id = user.id
    if not title:
        title = random_team_name()
    if not description:
        description = random_team_description()
    team_in = TeamCreate(title=title, description=description)
    return crud.team.create_with_owner(db=db, obj_in=team_in, owner_id=owner_id)
