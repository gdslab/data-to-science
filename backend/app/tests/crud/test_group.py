from sqlalchemy.orm import Session

from app import crud
from app.schemas.group import GroupCreate, GroupUpdate
from app.tests.utils.group import create_random_group
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_group_description, random_group_name


def test_create_group(db: Session) -> None:
    title = random_group_name()
    description = random_group_description()
    user = create_random_user(db)
    group = create_random_group(db, title=title, description=description, owner_id=user.id)
    assert group.title == title
    assert group.description == description
    assert group.owner_id == user.id


def test_get_group(db: Session) -> None:
    group = create_random_group(db)
    stored_group = crud.group.get(db=db, id=group.id)
    assert stored_group
    assert group.id == stored_group.id
    assert group.title == stored_group.title
    assert group.description == stored_group.description
    assert group.owner_id == stored_group.owner_id


def test_update_group(db: Session) -> None:
    group = create_random_group(db)
    new_description = random_group_description()
    group_in_update = GroupUpdate(description=new_description)
    group_update = crud.group.update(db=db, db_obj=group, obj_in=group_in_update)
    assert group.id == group_update.id
    assert group.title == group_update.title
    assert new_description == group_update.description
    assert group.owner_id == group_update.owner_id


def test_delete_group(db: Session) -> None:
    user = create_random_user(db)
    group = create_random_group(db, owner_id=user.id)
    group_removed = crud.group.remove(db=db, id=group.id)
    group_after_remove = crud.group.get(db=db, id=group.id)
    assert group_after_remove is None
    assert group_removed.id == group.id
    assert group_removed.title == group.title
    assert group_removed.description == group.description
    assert group_removed.owner_id == user.id
