import logging
from typing import Optional, Sequence
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import crud
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

    def read_by_user_id(
        self, db: Session, indoor_project_id: UUID, user_id: UUID
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
        """Read all existing indoor projects owned by user.

        Args:
            db (Session): Database session.
            user_id (UUID): ID of user indoor projects must belong to.

        Returns:
            Sequence[IndoorProject]: All indoor projects owned by user.
        """
        statement = select(IndoorProject).where(
            and_(IndoorProject.owner_id == user_id, IndoorProject.is_active)
        )

        with db as session:
            indoor_projects = session.scalars(statement).all()

            return indoor_projects

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
