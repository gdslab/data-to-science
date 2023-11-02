import logging
from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Bundle, Session
from sqlalchemy.sql.selectable import Select

from app.crud.base import CRUDBase
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.team_member import TeamMemberCreate, TeamMemberUpdate


logger = logging.getLogger("__name__")


class CRUDTeamMember(CRUDBase[TeamMember, TeamMemberCreate, TeamMemberUpdate]):
    def create_with_team(
        self, db: Session, *, obj_in: TeamMemberCreate, team_id: UUID
    ) -> TeamMember | None:
        obj_in_data = jsonable_encoder(obj_in)
        email = obj_in_data["email"]
        stmt = select(User).filter_by(email=email, is_approved=True)
        with db as session:
            user_obj = session.scalar(stmt)
            if user_obj:
                db_obj = self.model(member_id=user_obj.id, team_id=team_id)
                session.add(db_obj)
                session.commit()
                session.refresh(db_obj)
                set_name_and_email_attr(db_obj, user_obj)
            else:
                db_obj = None
            return db_obj

    def create_multi_with_team(
        self, db: Session, team_members: list[UUID], team_id: UUID
    ) -> Sequence[TeamMember]:
        with db as session:
            team_member_objs = []
            for user_id in team_members:
                team_member_objs.append({"member_id": user_id, "team_id": team_id})
            session.execute(
                insert(TeamMember).values(team_member_objs).on_conflict_do_nothing()
            )
            session.commit()
        return self.get_list_of_team_members(db, team_id=team_id)

    def get_team_member_by_email(
        self, db: Session, *, email: str, team_id: UUID
    ) -> TeamMember | None:
        """Find team member record by email."""
        stmt: Select = (
            select(
                TeamMember, Bundle("user", User.first_name, User.last_name, User.email)
            )
            .join(TeamMember.member)
            .where(User.email == email)
            .where(TeamMember.team_id == team_id)
        )
        with db as session:
            team_member = session.execute(stmt).one_or_none()
            if team_member:
                set_name_and_email_attr(team_member[0], team_member[1])
                return team_member[0]
        return None

    def get_team_member_by_id(
        self, db: Session, *, user_id: UUID, team_id: UUID
    ) -> TeamMember | None:
        """Find team member record by team id."""
        stmt: Select = (
            select(
                TeamMember, Bundle("user", User.first_name, User.last_name, User.email)
            )
            .join(TeamMember.member)
            .where(TeamMember.member_id == user_id)
            .where(TeamMember.team_id == team_id)
        )
        with db as session:
            team_member = session.execute(stmt).one_or_none()
            if team_member:
                set_name_and_email_attr(team_member[0], team_member[1])
                return team_member[0]
        return None

    def get_list_of_team_members(
        self, db: Session, *, team_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[TeamMember]:
        stmt: Select = (
            select(
                TeamMember, Bundle("user", User.first_name, User.last_name, User.email)
            )
            .join(TeamMember.member)
            .where(TeamMember.team_id == team_id)
            .offset(skip)
            .limit(limit)
        )
        team_members: list[TeamMember] = []
        with db as session:
            for team_member in session.execute(stmt).all():
                set_name_and_email_attr(team_member[0], team_member[1])
                team_members.append(team_member[0])

        return team_members


def set_name_and_email_attr(team_member_obj: TeamMember, user_obj: User):
    setattr(team_member_obj, "full_name", f"{user_obj.first_name} {user_obj.last_name}")
    setattr(team_member_obj, "email", user_obj.email)


team_member = CRUDTeamMember(TeamMember)
