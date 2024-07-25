import datetime
from typing import List

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.schemas.extension import ExtensionCreate
from app.schemas.team_extension import TeamExtensionUpdate
from app.schemas.user_extension import UserExtensionUpdate
from app.tests.utils.extension import (
    create_extension,
    create_team_extension,
    create_user_extension,
)
from app.tests.utils.team import create_team
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user


def test_create_extension(db: Session) -> None:
    extension_name = "ext1"
    extension_description = "Extension 1"
    extension_in = ExtensionCreate(
        name=extension_name, description=extension_description
    )
    extension = crud.extension.create_extension(db, extension_in=extension_in)
    assert extension
    assert extension.id
    assert extension.name == extension_name
    assert extension.description == extension_description


def test_create_duplicate_extension(db: Session) -> None:
    extension_name = "ext1"
    extension_description = "Extension 1"
    extension = create_extension(
        db, name=extension_name, description=extension_description
    )
    # unique contraint should cause creation duplicate extension to fail
    with pytest.raises(IntegrityError):
        extension_duplicate = create_extension(
            db, name=extension_name, description=extension_description
        )


def test_read_extension_by_name(db: Session) -> None:
    extension_name = "ext1"
    create_extension(db, name=extension_name)
    extension = crud.extension.get_extension_by_name(db, extension_name=extension_name)
    assert extension
    assert extension.name == extension_name


def test_read_extensions(db: Session) -> None:
    extension1 = create_extension(db, name="ext1", description="Extension 1")
    extension2 = create_extension(db, name="ext2", description="Extension 2")
    extension3 = create_extension(db, name="ext3", description="Extension 3")
    extensions = crud.extension.get_extensions(db)
    assert extensions
    assert isinstance(extensions, List)
    assert len(extensions) == 3
    for extension in extensions:
        assert extension.id in [extension1.id, extension2.id, extension3.id]


def test_update_team_extension(db: Session) -> None:
    extension = create_extension(db, name="ext1")
    team = create_team(db)
    team_extension_in = TeamExtensionUpdate(extension_id=extension.id, team_id=team.id)
    team_extension = crud.extension.create_or_update_team_extension(
        db, team_extension_in=team_extension_in
    )
    assert team_extension
    assert team_extension.id
    assert team_extension.is_active
    assert team_extension.extension_id == extension.id
    assert team_extension.team_id == team.id


def test_update_user_extension(db: Session) -> None:
    extension = create_extension(db, name="ext1")
    user = create_user(db)
    user_extension_in = UserExtensionUpdate(extension_id=extension.id, user_id=user.id)
    user_extension = crud.extension.create_or_update_user_extension(
        db, user_extension_in=user_extension_in
    )
    assert user_extension
    assert user_extension.id
    assert user_extension.is_active
    assert user_extension.extension_id == extension.id
    assert user_extension.user_id == user.id


def test_deactivate_team_extension(db: Session) -> None:
    extension = create_extension(db, name="ext1")
    team = create_team(db)
    create_team_extension(db, extension_id=extension.id, team_id=team.id)
    team_extension_in = TeamExtensionUpdate(
        is_active=False, extension_id=extension.id, team_id=team.id
    )
    team_extension = crud.extension.create_or_update_team_extension(
        db, team_extension_in=team_extension_in
    )
    assert team_extension
    assert team_extension.id
    assert not team_extension.is_active
    assert team_extension.extension_id == extension.id
    assert team_extension.team_id == team.id
    assert isinstance(team_extension.deactivated_at, datetime.datetime)
    assert team_extension.deactivated_at.replace(
        tzinfo=datetime.timezone.utc
    ) < datetime.datetime.now(datetime.UTC)


def test_deactivate_user_extension(db: Session) -> None:
    extension = create_extension(db, name="ext1")
    user = create_user(db)
    create_user_extension(db, extension_id=extension.id, user_id=user.id)
    user_extension_in = UserExtensionUpdate(
        is_active=False, extension_id=extension.id, user_id=user.id
    )
    user_extension = crud.extension.create_or_update_user_extension(
        db, user_extension_in=user_extension_in
    )
    assert user_extension
    assert user_extension.id
    assert not user_extension.is_active
    assert user_extension.extension_id == extension.id
    assert user_extension.user_id == user.id
    assert isinstance(user_extension.deactivated_at, datetime.datetime)
    assert user_extension.deactivated_at.replace(
        tzinfo=datetime.timezone.utc
    ) < datetime.datetime.now(datetime.UTC)


def test_read_team_extension(db: Session) -> None:
    extension = create_extension(db, name="ext1", description="Extension 1")
    team = create_team(db)
    team_extension = create_team_extension(
        db, extension_id=extension.id, team_id=team.id
    )
    team_extension_in_db = crud.extension.get_team_extension(
        db, extension_id=extension.id, team_id=team.id
    )
    assert team_extension_in_db
    assert team_extension_in_db.id == team_extension.id
    assert team_extension_in_db.extension_id == extension.id
    assert team_extension_in_db.team_id == team.id


def test_read_user_extension(db: Session) -> None:
    extension = create_extension(db, name="ext1", description="Extension 1")
    user = create_user(db)
    user_extension = create_user_extension(
        db, extension_id=extension.id, user_id=user.id
    )
    user_extension_in_db = crud.extension.get_user_extension(
        db, extension_id=extension.id, user_id=user.id
    )
    assert user_extension_in_db
    assert user_extension_in_db.id == user_extension.id
    assert user_extension_in_db.extension_id == extension.id
    assert user_extension_in_db.user_id == user.id


def test_read_team_extension_by_user(db: Session) -> None:
    extension = create_extension(db, name="ext1")
    user = create_user(db)
    team = create_team(db)
    team_member = create_team_member(db, email=user.email, team_id=team.id)
    team_extension = create_team_extension(
        db, extension_id=extension.id, team_id=team.id
    )
    team_extension_by_user = crud.extension.get_team_extension_by_user(
        db, extension_id=extension.id, user_id=user.id
    )
    assert team_extension_by_user
    assert team_extension_by_user.id == team_extension.id
    assert team_extension_by_user.extension_id == extension.id
    assert team_extension_by_user.team_id == team.id


def test_read_team_extension_does_not_return_inactive_extension(db: Session) -> None:
    extension = create_extension(db, name="ext1", description="Extension 1")
    team = create_team(db)
    create_team_extension(db, extension_id=extension.id, team_id=team.id)
    team_extension_in = TeamExtensionUpdate(
        is_active=False, extension_id=extension.id, team_id=team.id
    )
    team_extension = crud.extension.create_or_update_team_extension(
        db, team_extension_in=team_extension_in
    )
    team_extension_in_db = crud.extension.get_team_extension(
        db, extension_id=extension.id, team_id=team.id
    )
    assert team_extension_in_db is None


def test_read_user_extension_does_not_return_inactive_extension(db: Session) -> None:
    extension = create_extension(db, name="ext1", description="Extension 1")
    user = create_user(db)
    create_user_extension(db, extension_id=extension.id, user_id=user.id)
    user_extension_in = UserExtensionUpdate(
        is_active=False, extension_id=extension.id, user_id=user.id
    )
    user_extension = crud.extension.create_or_update_user_extension(
        db, user_extension_in=user_extension_in
    )
    user_extension_in_db = crud.extension.get_user_extension(
        db, extension_id=extension.id, user_id=user.id
    )
    assert user_extension_in_db is None


def test_removing_extension_removes_related_team_and_user_extensions(
    db: Session,
) -> None:
    extension = create_extension(db, name="ext1", description="Extension 1")
    team = create_team(db)
    team_extension = create_team_extension(
        db, extension_id=extension.id, team_id=team.id
    )
    user = create_user(db)
    user_extension = create_user_extension(
        db, extension_id=extension.id, user_id=user.id
    )
    extension_removed = crud.extension.remove(db, id=extension.id)
    team_extension_after_remove = crud.extension.get_team_extension(
        db, extension_id=extension.id, team_id=team.id
    )
    user_extension_after_remove = crud.extension.get_user_extension(
        db, extension_id=extension.id, user_id=user.id
    )
    assert team_extension
    assert team_extension_after_remove is None
    assert user_extension
    assert user_extension_after_remove is None
