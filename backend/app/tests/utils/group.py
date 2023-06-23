from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.group import GroupCreate
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_group_name, random_group_description


def create_random_group(
    db: Session,
    *, 
    title: str | None = None,
    description: str | None = None,
    owner_id: int | None = None
) -> models.Group:
    if owner_id is None:
        user = create_random_user(db)
        owner_id = user.id
    if not title:
        title = random_group_name()
    if not description:
        description = random_group_description()
    group_in = GroupCreate(title=title, description=description)
    return crud.group.create_with_owner(db=db, obj_in=group_in, owner_id=owner_id)
