from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.extension import Extension
from app.models.team_extension import TeamExtension
from app.models.user_extension import UserExtension
from app.schemas.extension import ExtensionCreate, ExtensionUpdate
from app.schemas.team_extension import TeamExtensionUpdate
from app.schemas.user_extension import UserExtensionUpdate


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

    def update_team_extension(
        self, db: Session, team_extension_in: TeamExtensionUpdate
    ) -> TeamExtension:
        pass

    def update_user_extension(
        self, db: Session, user_extension_in: UserExtensionUpdate
    ) -> UserExtension:
        pass


extension = CRUDExtension(Extension)
