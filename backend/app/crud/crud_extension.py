from typing import List

from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.extension import Extension
from app.models.team_extension import TeamExtension
from app.models.user_extension import UserExtension
from app.schemas.extension import ExtensionCreate, ExtensionUpdate
from app.schemas.team_extension import TeamExtensionUpdate
from app.schemas.user_extension import UserExtensionUpdate
from app.models.utils.user import utcnow


class CRUDExtension(CRUDBase[Extension, ExtensionCreate, ExtensionUpdate]):
    def create_extension(self, db: Session, extension_in: ExtensionCreate) -> Extension:
        extension = self.model(**extension_in.model_dump())
        with db as session:
            session.add(extension)
            session.commit()
            session.refresh(extension)
            return extension

    def get_extensions(self, db: Session) -> List[Extension]:
        select_statement = select(Extension)

        with db as session:
            extensions = session.scalars(select_statement).all()
            return extensions

    def create_or_update_team_extension(
        self, db: Session, team_extension_in: TeamExtensionUpdate
    ) -> TeamExtension:
        extension_id = team_extension_in.extension_id
        team_id = team_extension_in.team_id

        select_statement = select(TeamExtension).where(
            and_(
                TeamExtension.extension_id == extension_id,
                TeamExtension.team_id == team_id,
            )
        )

        with db as session:
            existing_team_extension = session.scalar(select_statement)
            if existing_team_extension:
                if not team_extension_in.is_active:
                    team_extension_in.deactivated_at = utcnow()
                team_extension = crud.extension.update(
                    db, db_obj=existing_team_extension, obj_in=team_extension_in
                )
            else:
                team_extension_in.is_active = True
                team_extension = TeamExtension(**team_extension_in.model_dump())
                with db as session:
                    session.add(team_extension)
                    session.commit()
                    session.refresh(team_extension)

            return team_extension

    def create_or_update_user_extension(
        self, db: Session, user_extension_in: UserExtensionUpdate
    ) -> UserExtension:
        extension_id = user_extension_in.extension_id
        user_id = user_extension_in.user_id

        select_statement = select(UserExtension).where(
            and_(
                UserExtension.extension_id == extension_id,
                UserExtension.user_id == user_id,
            )
        )

        with db as session:
            existing_user_extension = session.scalar(select_statement)
            if existing_user_extension:
                if not user_extension_in.is_active:
                    user_extension_in.deactivated_at = utcnow()
                user_extension = crud.extension.update(
                    db, db_obj=existing_user_extension, obj_in=user_extension_in
                )
            else:
                user_extension_in.is_active = True
                user_extension = UserExtension(**user_extension_in.model_dump())
                with db as session:
                    session.add(user_extension)
                    session.commit()
                    session.refresh(user_extension)

            return user_extension


extension = CRUDExtension(Extension)
