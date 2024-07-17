from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session

from app import crud
from app.crud.base import CRUDBase
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.team import Team
from app.models.team_extension import TeamExtension
from app.models.team_member import TeamMember
from app.schemas.project import ProjectUpdate
from app.schemas.team import TeamCreate, TeamUpdate


class CRUDTeam(CRUDBase[Team, TeamCreate, TeamUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: TeamCreate, owner_id: UUID
    ) -> Team:
        """Create new team and add user as team member."""
        # separate out team object, team member ids, and project id
        obj_in_data = jsonable_encoder(obj_in)
        team_in_data = {
            "title": obj_in_data.get("title"),
            "description": obj_in_data.get("description"),
        }
        team_member_ids = obj_in_data.get("new_members")
        project_id = obj_in_data.get("project")
        # add team object
        team_db_obj = self.model(**team_in_data, owner_id=owner_id)
        with db as session:
            session.add(team_db_obj)
            session.commit()
            session.refresh(team_db_obj)
        # add team member objects
        new_team_members = []
        # create empty list if new_members not provided by obj_in
        if not team_member_ids:
            team_member_ids = []
        # confirm owner_id is present in team_members ids and add it if not
        if str(owner_id) not in team_member_ids:
            team_member_ids.append(str(owner_id))
        # iterate over team member ids and create team member objects
        if len(team_member_ids) > 0:
            for user_id in team_member_ids:
                new_team_members.append(
                    TeamMember(member_id=user_id, team_id=team_db_obj.id)
                )
            with db as session:
                session.add_all(new_team_members)
                session.commit()
                for team_member in new_team_members:
                    session.refresh(team_member)
        # add project object (if any)
        if project_id:
            project_obj = crud.project.get(db, id=project_id)
            if project_obj and not project_obj.team_id:
                crud.project.update_project(
                    db,
                    project_obj=project_obj,
                    project_in=ProjectUpdate(team_id=team_db_obj.id),
                    project_id=project_id,
                    user_id=owner_id,
                )
        return team_db_obj

    def get_team(
        self, db: Session, *, user_id: UUID, team_id: UUID, permission="read"
    ) -> Team | None:
        """Retrieve team by id. User must be member of team."""
        if permission == "readwrite":
            stmt = (
                select(Team)
                .join(TeamMember.team)
                .where(TeamMember.member_id == user_id)
                .where(TeamMember.team_id == team_id)
                .where(Team.owner_id == user_id)
            )
        else:
            stmt = (
                select(Team)
                .join(TeamMember.team)
                .where(TeamMember.member_id == user_id)
                .where(TeamMember.team_id == team_id)
            )
        with db as session:
            team = session.scalar(stmt)
            if team:
                setattr(
                    team,
                    "exts",
                    [item.extension.name for item in team.extensions if item.is_active],
                )
                setattr(team, "is_owner", user_id == team.owner_id)

        return team

    def get_user_team_list(
        self,
        db: Session,
        *,
        user_id: UUID,
        owner_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Team]:
        """List of teams the user belongs to."""
        if owner_only:
            statement = (
                select(Team)
                .join(TeamMember.team)
                .where(TeamMember.member_id == user_id)
                .where(TeamMember.member_id == Team.owner_id)
                .offset(skip)
                .limit(limit)
            )
        else:
            statement = (
                select(Team)
                .join(TeamMember.team)
                .where(TeamMember.member_id == user_id)
                .offset(skip)
                .limit(limit)
            )
        with db as session:
            teams = session.scalars(statement).unique().all()
            # indicate if team member is also team owner
            for team in teams:
                setattr(
                    team,
                    "exts",
                    [item.extension.name for item in team.extensions if item.is_active],
                )
                setattr(team, "is_owner", user_id == team.owner_id)
        return teams

    def delete_team(self, db: Session, team_id: UUID) -> Team | None:
        # delete team
        with db as session:
            team = session.get(self.model, team_id)
            session.delete(team)
            session.commit()

        return team


team = CRUDTeam(Team)
