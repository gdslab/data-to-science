from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.team import Team
from app.models.team_member import TeamMember
from app.schemas.project import ProjectUpdate
from app.schemas.team import TeamCreate, TeamUpdate
from app.schemas.team_member import Role


class CRUDTeam(CRUDBase[Team, TeamCreate, TeamUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: TeamCreate, owner_id: UUID
    ) -> Team:
        """Create new team and add user as team member."""
        # Separate out team object, team member ids, and project id
        team_in_data = {
            "title": obj_in.title,
            "description": obj_in.description,
        }
        team_member_ids = obj_in.new_members
        project_id = obj_in.project

        # Check if project_id exists and user is an owner of the project
        if project_id:
            # Convert project_id to UUID if it is a string
            if not isinstance(project_id, UUID):
                project_id = UUID(project_id)
            # Check if project exists
            project = crud.project.get(db, id=project_id)
            if not project:
                raise ValueError("Project not found")
            # Create list of project owner ids
            project_owners = crud.project_member.get_list_of_project_members(
                db, project_uuid=project.id, role=Role.OWNER
            )
            project_owner_ids = [str(po.member_id) for po in project_owners]
            # Check if user is an owner of the project
            if str(owner_id) not in project_owner_ids:
                raise ValueError("User is not an owner of the project")

        # Add team object
        with db as session:
            team_db_obj = Team(**team_in_data, owner_id=owner_id)
            session.add(team_db_obj)
            session.commit()
            session.refresh(team_db_obj)

        # Add team member objects
        new_team_members = []

        # Create empty list if new_members not provided by obj_in
        if not team_member_ids:
            team_member_ids_str: List[str] = []
        else:
            team_member_ids_str = [str(mid) for mid in team_member_ids]

        # Confirm owner_id is present in team_members ids and add it if not
        if str(owner_id) not in team_member_ids_str:
            team_member_ids_str.append(str(owner_id))

        # Create team member objects
        if len(team_member_ids_str) > 0:
            for user_id in team_member_ids_str:
                if user_id == str(owner_id):
                    role = Role.OWNER
                else:
                    role = Role.VIEWER
                new_team_members.append(
                    TeamMember(member_id=user_id, team_id=team_db_obj.id, role=role)
                )
            # Add team members to database
            with db as session:
                session.add_all(new_team_members)
                session.commit()

        # Add project
        if project_id:
            # Convert to UUID if project ID is string
            if isinstance(project_id, str):
                project_id = UUID(project_id)

            # Get project object
            project = crud.project.get(db, id=project_id)

            if not project:
                raise ValueError("Project not found")

            if project.team_id:
                raise ValueError("Project already has a team")

            # Update project with team_id
            crud.project.update_project(
                db,
                project_id=project_id,
                project_in=ProjectUpdate(team_id=team_db_obj.id),
                project_obj=project,
                user_id=owner_id,
            )

        return team_db_obj

    def get_team(
        self, db: Session, *, user_id: UUID, team_id: UUID, permission: str = "read"
    ) -> Optional[Team]:
        """Retrieve team by id. User must be member of team."""
        if permission == "readwritedelete":
            statement = (
                select(Team)
                .join(TeamMember.team)
                .where(
                    and_(
                        TeamMember.member_id == user_id,
                        TeamMember.team_id == team_id,
                        TeamMember.role == Role.OWNER,
                    )
                )
            )
        elif permission == "readwrite":
            statement = (
                select(Team)
                .join(TeamMember.team)
                .where(
                    and_(
                        TeamMember.member_id == user_id,
                        TeamMember.team_id == team_id,
                        TeamMember.role.in_([Role.MANAGER, Role.OWNER]),
                    )
                )
            )
        else:
            statement = (
                select(Team)
                .join(TeamMember.team)
                .where(
                    and_(TeamMember.member_id == user_id, TeamMember.team_id == team_id)
                )
            )
        with db as session:
            team = session.scalar(statement)
            if team:
                setattr(
                    team,
                    "exts",
                    [item.extension.name for item in team.extensions if item.is_active],
                )
                setattr(team, "is_owner", user_id == team.owner_id)

        return team

    def get_user_team_list(
        self, db: Session, *, user_id: UUID, owner_only: bool = False
    ) -> Sequence[Team]:
        """List of teams the user belongs to."""
        if owner_only:
            statement = (
                select(Team)
                .join(TeamMember.team)
                .where(
                    and_(
                        TeamMember.member_id == user_id,
                        or_(
                            TeamMember.role == Role.OWNER,
                            TeamMember.role == Role.MANAGER,
                        ),
                    )
                )
            )
        else:
            statement = (
                select(Team)
                .join(TeamMember.team)
                .where(TeamMember.member_id == user_id)
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

    def update_team(
        self, db: Session, team_in: TeamUpdate, team_id: UUID, user_id: UUID
    ) -> Optional[Team]:
        with db as session:
            team = session.get(Team, team_id)
            if not team:
                return None

            # Check if user is project owner
            if team_in.project:
                if not isinstance(team_in.project, UUID):
                    project_id = UUID(team_in.project)
                else:
                    project_id = team_in.project
                project = crud.project.get(db, id=project_id)
                if not project:
                    return None
                project_owners = crud.project_member.get_list_of_project_members(
                    db, project_uuid=project.id, role=Role.OWNER
                )
                project_owner_ids = [str(po.member_id) for po in project_owners]
                if str(user_id) not in project_owner_ids:
                    return None

            # Update team
            updated_team = crud.team.update(db, db_obj=team, obj_in=team_in)

            # Set is_owner attribute
            setattr(updated_team, "is_owner", user_id == updated_team.owner_id)

            return updated_team

    def delete_team(self, db: Session, team_id: UUID) -> Optional[Team]:
        # delete team
        with db as session:
            team = session.get(self.model, team_id)
            session.delete(team)
            session.commit()

        return team


team = CRUDTeam(Team)
