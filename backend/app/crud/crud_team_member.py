import logging
from typing import List, Optional, Sequence, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import update, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Bundle, Session
from sqlalchemy.sql.selectable import Select

from app import crud
from app.core.config import settings
from app.crud.base import CRUDBase
from app.crud.crud_user import find_profile_img
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.project_member import ProjectMemberCreate
from app.schemas.role import Role
from app.schemas.team_member import TeamMemberCreate, TeamMemberUpdate


logger = logging.getLogger("__name__")


class CRUDTeamMember(CRUDBase[TeamMember, TeamMemberCreate, TeamMemberUpdate]):
    def create_with_team(
        self, db: Session, *, obj_in: TeamMemberCreate, team_id: UUID
    ) -> Optional[TeamMember]:
        """Creates a new team member record. If the team member is the team
        owner, the role is set to "owner". Otherwise, the role is set to
        "member". If the team is associated with a project, the team member
        is added as a project member.

        Args:
            db (Session): Database session.
            obj_in (TeamMemberCreate): Team member object.
            team_id (UUID): Team ID.

        Raises:
            ValueError: Raised if user is not found or not active.
            ValueError: Raised if team is not found.

        Returns:
            Optional[TeamMember]: Team member object or None.
        """
        # Query user by email
        with db as session:
            user_select_statement = select(User).where(
                User.email == obj_in.email,
                User.is_approved == True,
                User.is_email_confirmed,
            )
            user_obj = session.scalar(user_select_statement)
            if not user_obj:
                return None

        # Query team by id
        with db as session:
            team = crud.team.get(db, id=team_id)
            if not team:
                return None

        # Check if user is team owner
        is_team_owner = team.owner_id == user_obj.id

        # Query team member by team id and user id
        with db as session:
            if is_team_owner:
                role = Role.OWNER
            else:
                role = obj_in.role
            team_member = TeamMember(member_id=user_obj.id, team_id=team_id, role=role)
            session.add(team_member)
            session.commit()
            session.refresh(team_member)
            set_name_and_email_attr(team_member, user_obj)

        # If team is associated with project, add this user as a project member
        with db as session:
            project_select_statement = select(Project).where(Project.team_id == team_id)
            project = session.scalar(project_select_statement)
            if project:
                # Check if user already project member
                project_member = crud.project_member.get_by_project_and_member_id(
                    db, project_id=project.id, member_id=user_obj.id
                )
                # Add as project member if not already
                if not project_member:
                    # Set project role to owner if this user is team owner
                    if is_team_owner:
                        project_role = "owner"
                    else:
                        project_role = "viewer"
                    # Create project member
                    crud.project_member.create_with_project(
                        db,
                        obj_in=ProjectMemberCreate(
                            member_id=user_obj.id, role=project_role
                        ),
                        project_id=project.id,
                    )
                else:
                    # Elevate project member role to "owner" if user is team owner
                    if is_team_owner:
                        project_member.role = Role.OWNER
                        session.commit()

        return team_member

    def create_multi_with_team(
        self, db: Session, team_members: list[UUID], team_id: UUID
    ) -> Sequence[TeamMember]:
        """Create multiple team members for a team. If a team member is the team
        owner, the role is set to "owner". Otherwise, the role is set to "member".
        If the team is associated with a project, the team members are added as
        project members.

        Args:
            db (Session): Database session.
            team_members (list[UUID]): Team member IDs.
            team_id (UUID): Team ID.

        Raises:
            ValueError: Raised if team not found.

        Returns:
            Sequence[TeamMember]: Team members.
        """
        # Query team by id
        team = crud.team.get(db, id=team_id)
        # Raise exception if team not found
        if not team:
            raise ValueError("Team not found")

        # Create unique list of team members to be added
        new_team_members = list(set(team_members))

        # Create team member objects
        team_member_objs: List[TeamMember] = []
        for user_id in new_team_members:
            # Check if user is team owner
            is_team_owner = team.owner_id == user_id
            # Skip if user is team owner
            if not is_team_owner:
                team_member_obj = TeamMember(member_id=user_id, team_id=team_id)
                team_member_objs.append(team_member_obj)

        # Add team member objects
        with db as session:
            session.add_all(team_member_objs)
            session.commit()

            # Select projects associated with team
            project_select_statement = select(Project).where(Project.team_id == team_id)
            projects = session.scalars(project_select_statement).all()
            if len(projects) > 0:
                for project in projects:
                    crud.project_member.create_multi_with_project(
                        db,
                        new_members=[
                            (team_member.member_id, team_member.role)
                            for team_member in team_member_objs
                        ],
                        project_id=project.id,
                    )

            # Return list of team members
            return self.get_list_of_team_members(db, team_id=team_id)

    def get_team_member_by_email(
        self, db: Session, *, email: str, team_id: UUID
    ) -> Optional[TeamMember]:
        """Find team member record by email.

        Args:
            db (Session): Database session.
            email (str): User email address.
            team_id (UUID): Team ID.

        Returns:
            Optional[TeamMember]: Team member object or None.
        """
        with db as session:
            # Select team member by email
            statement: Select = (
                select(
                    TeamMember,
                    Bundle(
                        "user", User.id, User.first_name, User.last_name, User.email
                    ),
                )
                .join(TeamMember.member)
                .where(User.email == email)
                .where(TeamMember.team_id == team_id)
            )
            team_member = session.execute(statement).one_or_none()

            # Return team member if found after setting email, name, and url attributes
            if team_member:
                set_name_and_email_attr(team_member[0], team_member[1])
                set_url_attr(team_member[0], team_member[1])
                return team_member[0]
            else:
                return None

    def get_team_member_by_id(
        self, db: Session, *, user_id: UUID, team_id: UUID
    ) -> Optional[TeamMember]:
        """Find team member record by user ID.

        Args:
            db (Session): Database session.
            user_id (UUID): User ID.
            team_id (UUID): Team ID.

        Returns:
            Optional[TeamMember]: Team member object or None.
        """
        with db as session:
            # Select team member by id
            statement: Select = (
                select(
                    TeamMember,
                    Bundle(
                        "user", User.id, User.first_name, User.last_name, User.email
                    ),
                )
                .join(TeamMember.member)
                .where(TeamMember.member_id == user_id)
                .where(TeamMember.team_id == team_id)
            )
            team_member = session.execute(statement).one_or_none()

            # Return team member if found after setting email, name, and url attributes
            if team_member:
                set_name_and_email_attr(team_member[0], team_member[1])
                set_url_attr(team_member[0], team_member[1])
                return team_member[0]
            else:
                return None

    def get_list_of_team_members(
        self, db: Session, *, team_id: UUID
    ) -> Sequence[TeamMember]:
        """List of team members by team id.

        Args:
            db (Session): Database session.
            team_id (UUID): Team ID.
        Returns:
            Sequence[TeamMember]: Team members.
        """
        with db as session:
            # Select team members by team id
            statement: Select = (
                select(
                    TeamMember,
                    Bundle(
                        "user", User.id, User.first_name, User.last_name, User.email
                    ),
                )
                .join(TeamMember.member)
                .where(TeamMember.team_id == team_id)
            )

            # Create list of team members
            team_members: list[TeamMember] = []
            for team_member in session.execute(statement).all():
                set_name_and_email_attr(team_member[0], team_member[1])
                set_url_attr(team_member[0], team_member[1])
                team_members.append(team_member[0])

            # Return list of team members
            return team_members

    def update_team_member(
        self, db: Session, team_member_in: TeamMemberUpdate, team_member_id: UUID
    ) -> Optional[TeamMember]:
        """Update team member role. If the team member role is changed, the
        project members role is also updated.

        Args:
            db (Session): Database session.
            team_member_in (TeamMemberUpdate): Team member update object.
            team_member_id (UUID): Team member ID.

        Returns:
            Optional[TeamMember]: Updated team member or None.
        """
        with db as session:
            statement = select(TeamMember).where(TeamMember.id == team_member_id)
            team_member = session.scalar(statement)
            if team_member:
                # Get previous team member role
                previous_team_member_role = team_member.role
                team = session.scalar(
                    select(Team).where(Team.id == team_member.team_id)
                )
                # Return None if team not found or team member is the team creator
                if not team or team.owner_id == team_member.member_id:
                    return None

                # Update team member
                updated_team_member = crud.team_member.update(
                    db, db_obj=team_member, obj_in=team_member_in
                )
                # Check if team member role changed
                if previous_team_member_role != updated_team_member.role:
                    # Find all projects associated with team
                    project_ids = session.scalars(
                        select(Project.id).where(Project.team_id == team_member.team_id)
                    ).all()
                    if project_ids:
                        # Update project members role
                        bulk_update_project_members = (
                            update(ProjectMember)
                            .where(ProjectMember.project_id.in_(project_ids))
                            .where(ProjectMember.member_id == team_member.member_id)
                            .values(role=updated_team_member.role)
                        )
                        session.execute(bulk_update_project_members)

                session.commit()

                return updated_team_member
            else:
                return None

    def remove_team_member(
        self, db: Session, member_id: UUID, team_id: UUID
    ) -> Optional[TeamMember]:
        """Remove team member from team.

        Args:
            db (Session): Database session.
            member_id (UUID): Team member ID.
            team_id (UUID): Team ID.

        Returns:
            Optional[TeamMember]: Removed team member or None.
        """
        with db as session:
            # Select team member by id
            statement = (
                select(TeamMember)
                .join(TeamMember.team)
                .where(TeamMember.member_id == member_id)
                .where(TeamMember.team_id == team_id)
                .where(Team.owner_id != member_id)
            )
            team_member = session.scalar(statement)
            # Delete team member if found
            if team_member:
                session.delete(team_member)
                session.commit()

                # Return team member if found
                return team_member
            else:
                return None


def set_name_and_email_attr(
    member_obj: Union[ProjectMember, TeamMember], user_obj: User
) -> None:
    """Add full name and email as attributes to project or team member
    object returned by API.

    Args:
        member_obj (Union[ProjectMember, TeamMember]): Project or team member object.
        user_obj (User): User object.
    """
    setattr(member_obj, "full_name", f"{user_obj.first_name} {user_obj.last_name}")
    setattr(member_obj, "email", user_obj.email)


def set_url_attr(team_member_obj: TeamMember, user_obj: User) -> None:
    """Add profile URL as attribute to team member object returned by API.

    Args:
        team_member_obj (TeamMember): Team member object.
        user_obj (User): User object.
    """
    profile_img = find_profile_img(str(user_obj.id))
    static_url = settings.API_DOMAIN + settings.STATIC_DIR

    if profile_img:
        profile_url = f"{static_url}/users/{str(user_obj.id)}/{profile_img}"
        setattr(team_member_obj, "profile_url", profile_url)
    else:
        setattr(team_member_obj, "profile_url", None)


team_member = CRUDTeamMember(TeamMember)
