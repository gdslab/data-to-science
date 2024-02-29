import logging
from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Bundle, Session
from sqlalchemy.sql.selectable import Select

from app import crud
from app.core.config import settings
from app.crud.base import CRUDBase
from app.crud.crud_user import find_profile_img
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.project_member import ProjectMemberCreate
from app.schemas.team_member import TeamMemberCreate, TeamMemberUpdate


logger = logging.getLogger("__name__")


class CRUDTeamMember(CRUDBase[TeamMember, TeamMemberCreate, TeamMemberUpdate]):
    def create_with_team(
        self, db: Session, *, obj_in: TeamMemberCreate, team_id: UUID
    ) -> TeamMember | None:
        # create team member
        obj_in_data = jsonable_encoder(obj_in)
        email = obj_in_data["email"]
        statement = select(User).filter_by(email=email, is_approved=True)
        team_member = None
        with db as session:
            user_obj = session.scalar(statement)
            if user_obj:
                team_member = self.model(member_id=user_obj.id, team_id=team_id)
                session.add(team_member)
                session.commit()
                session.refresh(team_member)
                set_name_and_email_attr(team_member, user_obj)
        # add as project member if team is associated with project
        statement = select(Project).where(Project.team_id == team_id)
        with db as session:
            project = session.scalar(statement)
            if project:
                project_member = crud.project_member.get_by_project_and_member_id(
                    db, project_id=project.id, member_id=user_obj.id
                )
                if not project_member:
                    crud.project_member.create_with_project(
                        db,
                        obj_in=ProjectMemberCreate(
                            member_id=user_obj.id, role="viewer"
                        ),
                        project_id=project.id,
                    )

        return team_member

    def create_multi_with_team(
        self, db: Session, team_members: list[UUID], team_id: UUID
    ) -> Sequence[TeamMember]:
        team = crud.team.get(db, id=team_id)
        team_members = list(set(team_members))
        if team:
            with db as session:
                team_member_objs = []
                for user_id in team_members:
                    if user_id != team.owner_id:
                        team_member_objs.append(
                            {"member_id": user_id, "team_id": team_id}
                        )
                session.execute(insert(TeamMember).values(team_member_objs))
                session.commit()
            # add as project members if team is associated with project
            project_query = select(Project).where(Project.team_id == team_id)
            with db as session:
                project = session.scalar(project_query)
                if project:
                    crud.project_member.create_multi_with_project(
                        db, member_ids=team_members, project_id=project.id
                    )

        return self.get_list_of_team_members(db, team_id=team_id)

    def get_team_member_by_email(
        self, db: Session, *, email: str, team_id: UUID
    ) -> TeamMember | None:
        """Find team member record by email."""
        stmt: Select = (
            select(
                TeamMember,
                Bundle("user", User.id, User.first_name, User.last_name, User.email),
            )
            .join(TeamMember.member)
            .where(User.email == email)
            .where(TeamMember.team_id == team_id)
        )
        team = crud.team.get(db, id=team_id)
        if not team:
            return []
        with db as session:
            team_member = session.execute(stmt).one_or_none()
            if team_member:
                set_name_and_email_attr(team_member[0], team_member[1])
                set_role_attr(team_member[0], team.owner_id)
                set_url_attr(team_member[0], team_member[1])
                return team_member[0]
        return None

    def get_team_member_by_id(
        self, db: Session, *, user_id: UUID, team_id: UUID
    ) -> TeamMember | None:
        """Find team member record by team id."""
        stmt: Select = (
            select(
                TeamMember,
                Bundle("user", User.id, User.first_name, User.last_name, User.email),
            )
            .join(TeamMember.member)
            .where(TeamMember.member_id == user_id)
            .where(TeamMember.team_id == team_id)
        )
        team = crud.team.get(db, id=team_id)
        if not team:
            return []
        with db as session:
            team_member = session.execute(stmt).one_or_none()
            if team_member:
                set_name_and_email_attr(team_member[0], team_member[1])
                set_role_attr(team_member[0], team.owner_id)
                set_url_attr(team_member[0], team_member[1])
                return team_member[0]
        return None

    def get_list_of_team_members(
        self, db: Session, *, team_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[TeamMember]:
        stmt: Select = (
            select(
                TeamMember,
                Bundle("user", User.id, User.first_name, User.last_name, User.email),
            )
            .join(TeamMember.member)
            .where(TeamMember.team_id == team_id)
            .offset(skip)
            .limit(limit)
        )
        team = crud.team.get(db, id=team_id)
        if not team:
            return []
        team_members: list[TeamMember] = []
        with db as session:
            for team_member in session.execute(stmt).all():
                set_name_and_email_attr(team_member[0], team_member[1])
                set_role_attr(team_member[0], team.owner_id)
                set_url_attr(team_member[0], team_member[1])
                team_members.append(team_member[0])

        return team_members

    def remove_team_member(
        self, db: Session, member_id: UUID, team_id: UUID
    ) -> TeamMember:
        # remove team member
        statement = (
            select(TeamMember)
            .where(TeamMember.member_id == member_id)
            .where(TeamMember.team_id == team_id)
        )
        with db as session:
            team_member = session.scalar(statement)
            if team_member:
                session.delete(team_member)
                session.commit()

        return team_member


def set_name_and_email_attr(team_member_obj: TeamMember, user_obj: User):
    setattr(team_member_obj, "full_name", f"{user_obj.first_name} {user_obj.last_name}")
    setattr(team_member_obj, "email", user_obj.email)


def set_url_attr(team_member_obj: TeamMember, user_obj: User) -> None:
    profile_img = find_profile_img(str(user_obj.id))
    static_url = settings.API_DOMAIN + settings.STATIC_DIR

    if profile_img:
        profile_url = f"{static_url}/users/{str(user_obj.id)}/{profile_img}"
        setattr(team_member_obj, "profile_url", profile_url)
    else:
        setattr(team_member_obj, "profile_url", None)


def set_role_attr(team_member_obj: TeamMember, owner_id: UUID):
    if team_member_obj.member_id == owner_id:
        setattr(team_member_obj, "role", "owner")
    else:
        setattr(team_member_obj, "role", "member")


team_member = CRUDTeamMember(TeamMember)
