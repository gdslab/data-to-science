from pydantic import UUID4
from sqlalchemy.orm import Session

from app import crud
from app.models.extension import Extension
from app.models.team_extension import TeamExtension
from app.models.user_extension import UserExtension
from app.schemas.extension import ExtensionCreate
from app.schemas.team_extension import TeamExtensionUpdate
from app.schemas.user_extension import UserExtensionUpdate


def create_extension(
    db: Session, name: str = "ext1", description: str = "Extension 1"
) -> Extension:
    extension_in = ExtensionCreate(description=description, name=name)
    extension = crud.extension.create_extension(db, extension_in=extension_in)
    return extension


def create_team_extension(
    db: Session, extension_id: UUID4, team_id: UUID4
) -> TeamExtension:
    team_extension_in = TeamExtensionUpdate(extension_id=extension_id, team_id=team_id)
    team_extension = crud.extension.create_or_update_team_extension(
        db, team_extension_in=team_extension_in
    )
    return team_extension


def create_user_extension(
    db: Session, extension_id: UUID4, user_id: UUID4
) -> UserExtension:
    user_extension_in = UserExtensionUpdate(extension_id=extension_id, user_id=user_id)
    user_extension = crud.extension.create_or_update_user_extension(
        db, user_extension_in=user_extension_in
    )
    return user_extension
