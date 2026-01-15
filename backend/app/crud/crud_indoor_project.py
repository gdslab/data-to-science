import logging
from typing import Optional, Sequence
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import crud
from app.core.exceptions import PermissionDenied, ResourceNotFound
from app.crud.base import CRUDBase
from app.models.indoor_project import IndoorProject
from app.models.project_member import ProjectMember
from app.models.project_type import ProjectType
from app.models.team_member import TeamMember
from app.models.utils.utcnow import utcnow
from app.schemas.indoor_project import (
    IndoorProjectCreate,
    IndoorProjectUpdate,
)
from app.schemas.role import Role
from app.utils.team_utils import is_team_owner


logger = logging.getLogger("__name__")


class CRUDIndoorProject(
    CRUDBase[IndoorProject, IndoorProjectCreate, IndoorProjectUpdate]
):
    def create_with_owner(
        self, db: Session, obj_in: IndoorProjectCreate, owner_id: UUID
    ) -> IndoorProject:
        """Create new indoor project and add user as project member.

        Args:
            db (Session): Database session.
            obj_in (IndoorProjectCreate): Creation model with indoor project attributes.
            owner_id (UUID): ID of user creating the indoor project.

        Returns:
            IndoorProject: Newly created indoor project.
        """
        obj_in_data = jsonable_encoder(obj_in)

        # Check if team was included and if user has the team member "owner" role
        team_members: Sequence[TeamMember] = []
        if obj_in_data.get("team_id"):
            team_members = crud.team_member.get_list_of_team_members(
                db, team_id=obj_in_data.get("team_id")
            )
            if len(team_members) < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Team does not have any members",
                )
            if not is_team_owner(owner_id, team_members, include_manager=True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Only team member with "owner" or "manager" role can perform this action',
                )

        # Create indoor project
        indoor_project_db_obj = self.model(**obj_in_data, owner_id=owner_id)
        with db as session:
            session.add(indoor_project_db_obj)
            session.commit()
            session.refresh(indoor_project_db_obj)

        # Add role attribute for API response
        setattr(indoor_project_db_obj, "role", "owner")

        # Add project member for the owner
        member_db_obj = ProjectMember(
            member_id=owner_id,
            project_type=ProjectType.INDOOR_PROJECT,
            project_uuid=indoor_project_db_obj.id,
            role=Role.OWNER,
        )
        with db as session:
            session.add(member_db_obj)
            session.commit()
            session.refresh(member_db_obj)

        # Add team members as project members
        if len(team_members) > 0:
            project_members = []
            for team_member in team_members:
                if team_member.member_id != owner_id:
                    project_members.append(
                        ProjectMember(
                            member_id=team_member.member_id,
                            project_type=ProjectType.INDOOR_PROJECT,
                            project_uuid=indoor_project_db_obj.id,
                            role=team_member.role,
                        )
                    )
            if len(project_members) > 0:
                with db as session:
                    session.add_all(project_members)
                    session.commit()

        return indoor_project_db_obj

    def get_with_permission(
        self,
        db: Session,
        indoor_project_id: UUID,
        user_id: UUID,
        required_permission: Role = Role.VIEWER,
    ) -> IndoorProject:
        """Get indoor project with permission check.

        Args:
            db (Session): Database session.
            indoor_project_id (UUID): ID of indoor project.
            user_id (UUID): ID of user.
            required_permission (Role): Minimum role required (VIEWER, MANAGER, or OWNER).

        Returns:
            IndoorProject: Indoor project if user has permission.

        Raises:
            ResourceNotFound: If project doesn't exist or is inactive.
            PermissionDenied: If user lacks required permission.
        """
        # Get project
        indoor_project = self.get(db, id=indoor_project_id)
        if not indoor_project or not indoor_project.is_active:
            raise ResourceNotFound("Indoor project")

        # Check if user is owner
        if indoor_project.owner_id == user_id:
            setattr(indoor_project, "role", Role.OWNER.value)
            return indoor_project

        # Check project membership for non-owners
        member = crud.project_member.get_by_project_and_member_id(
            db,
            project_uuid=indoor_project_id,
            member_id=user_id,
            project_type=ProjectType.INDOOR_PROJECT,
        )

        if not member:
            raise PermissionDenied("You are not a member of this indoor project")

        # Check role hierarchy: OWNER > MANAGER > VIEWER
        role_hierarchy = {Role.VIEWER: 1, Role.MANAGER: 2, Role.OWNER: 3}

        if role_hierarchy.get(member.role, 0) < role_hierarchy.get(
            required_permission, 999
        ):
            raise PermissionDenied(
                f"This action requires {required_permission.value} role or higher"
            )

        # Set the user's role on the indoor project for API response
        setattr(indoor_project, "role", member.role.value)

        return indoor_project

    def read_by_user_id(
        self,
        db: Session,
        indoor_project_id: UUID,
        user_id: UUID,
        permission: str = "read",
    ) -> Optional[IndoorProject]:
        """Read existing indoor project owned by user.

        Args:
            db (Session): Database session.
            indoor_project_id (UUID): ID of indoor project.
            user_id (UUID): ID of user indoor project must belong to.

        Returns:
            Optional[IndoorProject]: Indoor project owned by user.
        """
        statement = select(IndoorProject).where(
            and_(
                IndoorProject.id == indoor_project_id,
                IndoorProject.owner_id == user_id,
                IndoorProject.is_active,
            )
        )

        with db as session:
            indoor_project = session.scalar(statement)

            return indoor_project

    def read_multi_by_user_id(
        self, db: Session, user_id: UUID
    ) -> Sequence[IndoorProject]:
        """Read all existing indoor projects where user is a member.

        Returns projects where the user has any role (OWNER, MANAGER, or VIEWER).
        Sets the role attribute on each project based on user's membership.

        Args:
            db (Session): Database session.
            user_id (UUID): ID of user.

        Returns:
            Sequence[IndoorProject]: All indoor projects where user is a member.
        """
        statement = (
            select(IndoorProject, ProjectMember)
            .join(IndoorProject.indoor_members)
            .where(
                and_(
                    IndoorProject.is_active,
                    ProjectMember.member_id == user_id
                )
            )
        )

        with db as session:
            results = session.execute(statement).all()
            indoor_projects = []

            for indoor_project_obj, member_obj in results:
                # Set the user's role on the indoor project for API response
                setattr(indoor_project_obj, "role", member_obj.role.value)
                indoor_projects.append(indoor_project_obj)

            return indoor_projects

    def update_indoor_project(
        self,
        db: Session,
        indoor_project_id: UUID,
        indoor_project_obj: IndoorProject,
        indoor_project_in: IndoorProjectUpdate,
        user_id: UUID,
    ) -> IndoorProject:
        """Update indoor project and add team members as project members if a new team is being added.

        Args:
            db (Session): Database session.
            indoor_project_id (UUID): ID of indoor project to update.
            indoor_project_obj (IndoorProject): Indoor project object to update.
            indoor_project_in (IndoorProjectUpdate): Indoor project update object.
            user_id (UUID): ID of user updating indoor project.

        Returns:
            IndoorProject: Updated indoor project.
        """
        indoor_project_in_data = jsonable_encoder(indoor_project_in)

        # Only process team changes if a new team_id is provided and it's different from current
        if (
            indoor_project_in_data.get("team_id") is not None
            and indoor_project_obj.team_id != indoor_project_in_data["team_id"]
        ):
            team_members = crud.team_member.get_list_of_team_members(
                db, team_id=indoor_project_in_data["team_id"]
            )
            # Check permissions
            if len(team_members) == 0 or not is_team_owner(
                user_id, team_members, include_manager=True
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only team owner or manager can perform this action",
                )

            # Add team members as project members
            crud.project_member.create_multi_with_project(
                db,
                new_members=[
                    (team_member.member_id, team_member.role)
                    for team_member in team_members
                ],
                project_uuid=indoor_project_id,
                project_type=ProjectType.INDOOR_PROJECT,
            )

        # Finish updating indoor project
        updated_indoor_project = self.update(
            db, db_obj=indoor_project_obj, obj_in=indoor_project_in
        )

        # Get project role for user updating indoor project
        project_member = crud.project_member.get_by_project_and_member_id(
            db,
            project_uuid=indoor_project_id,
            member_id=user_id,
            project_type=ProjectType.INDOOR_PROJECT,
        )
        if project_member:
            setattr(updated_indoor_project, "role", project_member.role.value)
        else:
            setattr(updated_indoor_project, "role", "viewer")

        return updated_indoor_project

    def deactivate(
        self, db: Session, indoor_project_id: UUID
    ) -> Optional[IndoorProject]:
        """Deactivate existing indoor project.

        Args:
            db (Session): Database session.
            indoor_project_id (UUID): ID for indoor project being deactivated.

        Returns:
            Optional[IndoorProject]: Updated indoor project.
        """
        statement = select(IndoorProject).where(
            and_(IndoorProject.id == indoor_project_id, IndoorProject.is_active)
        )

        with db as session:
            indoor_project = session.scalar(statement)

            if indoor_project:
                indoor_project.is_active = False
                indoor_project.deactivated_at = utcnow()
                session.commit()
                session.refresh(indoor_project)

            return indoor_project


indoor_project = CRUDIndoorProject(IndoorProject)
