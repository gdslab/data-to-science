from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.extension import Extension
from app.models.team import Team
from app.models.team_extension import TeamExtension
from app.models.team_member import TeamMember
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

    def get_extension_by_name(
        self, db: Session, extension_name: str
    ) -> Optional[Extension]:
        select_statement = select(Extension).where(Extension.name == extension_name)

        with db as session:
            extension = session.scalar(select_statement)
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
                    team_extension_in.deactivated_at = datetime.now(tz=timezone.utc)
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
                    user_extension_in.deactivated_at = datetime.now(tz=timezone.utc)
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

    def get_team_extension(
        self, db: Session, extension_id: UUID, team_id: UUID
    ) -> Optional[TeamExtension]:
        select_statement = select(TeamExtension).where(
            and_(
                TeamExtension.extension_id == extension_id,
                TeamExtension.team_id == team_id,
                TeamExtension.is_active,
            )
        )

        with db as session:
            team_extension = session.scalar(select_statement)
            if team_extension:
                return team_extension

        return None

    def get_team_extension_by_user(
        self, db: Session, extension_id: UUID, user_id: UUID
    ) -> Optional[TeamExtension]:
        select_statement = (
            select(TeamExtension)
            .join(Team)
            .join(TeamMember)
            .where(
                and_(
                    TeamMember.member_id == user_id,
                    TeamExtension.extension_id == extension_id,
                    TeamExtension.is_active,
                )
            )
        )

        with db as session:
            team_extension = session.scalar(select_statement)
            if team_extension:
                return team_extension

        return None

    def get_user_extension(
        self, db: Session, extension_id: UUID, user_id: UUID
    ) -> Optional[UserExtension]:
        select_statement = select(UserExtension).where(
            and_(
                UserExtension.extension_id == extension_id,
                UserExtension.user_id == user_id,
                UserExtension.is_active,
            )
        )

        with db as session:
            user_extension = session.scalar(select_statement)
            if user_extension:
                return user_extension

        return None

    def get_user_extensions_list(self, db: Session, user_id: UUID) -> List[str]:
        select_user_extensions_statement = (
            select(Extension)
            .join(UserExtension)
            .where(UserExtension.user_id == user_id, UserExtension.is_active)
        )
        select_team_extesnions_statement = (
            select(Extension)
            .join(TeamExtension)
            .join(Team)
            .join(TeamMember)
            .where(and_(TeamMember.member_id == user_id, TeamExtension.is_active))
        )

        with db as session:
            # Get all extensions
            user_extensions = list(
                session.scalars(select_user_extensions_statement).all()
            )
            team_extensions = list(
                session.scalars(select_team_extesnions_statement).all()
            )

            # Get user's metashape and odm extensions
            user_metashape = any(ext.name == "metashape" for ext in user_extensions)
            user_odm = any(ext.name == "odm" for ext in user_extensions)

            # Get team's metashape extension
            team_metashape = any(ext.name == "metashape" for ext in team_extensions)

            # Handle precedence rules
            if user_metashape:
                # If user has metashape, remove odm from both lists
                user_extensions = [ext for ext in user_extensions if ext.name != "odm"]
                team_extensions = [ext for ext in team_extensions if ext.name != "odm"]
            elif user_odm:
                # If user has odm but not metashape, remove metashape from team extensions
                team_extensions = [
                    ext for ext in team_extensions if ext.name != "metashape"
                ]
            elif team_metashape:
                # If team has metashape and user has neither, remove odm from team extensions
                team_extensions = [ext for ext in team_extensions if ext.name != "odm"]

            # Combine and deduplicate extensions
            all_extensions = user_extensions + team_extensions
            extension_names = list(set(ext.name for ext in all_extensions))

            return extension_names


extension = CRUDExtension(Extension)
