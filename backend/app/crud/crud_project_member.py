from typing import List, Optional, Sequence, Tuple, TypedDict, Union
from uuid import UUID

from fastapi import status
from sqlalchemy import select, true
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Bundle, Session, joinedload
from sqlalchemy.sql.selectable import Select

from app import crud
from app.crud.base import CRUDBase
from app.crud.crud_team_member import set_name_and_email_attr, set_url_attr
from app.models.indoor_project import IndoorProject
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_type import ProjectType
from app.models.team import Team
from app.models.user import User
from app.schemas.project_member import ProjectMemberCreate, ProjectMemberUpdate
from app.schemas.team_member import Role


class UpdateProjectMember(TypedDict):
    response_code: int
    message: str
    result: ProjectMember | None


class CRUDProjectMember(
    CRUDBase[ProjectMember, ProjectMemberCreate, ProjectMemberUpdate]
):
    def create_with_project(
        self,
        db: Session,
        *,
        obj_in: ProjectMemberCreate,
        project_uuid: UUID,
        project_type: ProjectType = ProjectType.PROJECT,
    ) -> Optional[ProjectMember]:
        if obj_in.email:
            statement = select(User).where(
                User.email == obj_in.email, User.is_approved, User.is_email_confirmed
            )
        elif obj_in.member_id:
            statement = select(User).where(
                User.id == obj_in.member_id, User.is_approved, User.is_email_confirmed
            )
        else:
            raise ValueError("Either email or member_id must be provided")

        # Get user obj
        with db as session:
            user_obj = session.scalar(statement)
            if not user_obj:
                return None

        # Query project by id and type
        is_project_owner = False
        project = None
        indoor_project = None

        with db as session:
            if project_type == ProjectType.PROJECT:
                project = crud.project.get(db, id=project_uuid)
                if project:
                    is_project_owner = project.owner_id == user_obj.id
            elif project_type == ProjectType.INDOOR_PROJECT:
                indoor_project = crud.indoor_project.get(db, id=project_uuid)
                if indoor_project:
                    is_project_owner = indoor_project.owner_id == user_obj.id
            # For invalid project types, we don't return None here - let the database constraint handle it

            # Only check project existence for valid project types
            if project_type in [ProjectType.PROJECT, ProjectType.INDOOR_PROJECT]:
                if not (
                    project
                    or (project_type == ProjectType.INDOOR_PROJECT and indoor_project)
                ):
                    return None

        # Add project member
        with db as session:
            if is_project_owner:
                role = Role.OWNER
            elif obj_in.role:
                role = obj_in.role
            else:
                role = Role.VIEWER
            project_member = ProjectMember(
                member_id=user_obj.id,
                project_type=project_type,
                project_uuid=project_uuid,
                role=role,
            )
            session.add(project_member)
            session.commit()
            session.refresh(project_member)
            set_name_and_email_attr(project_member, user_obj)

        return project_member

    def create_multi_with_project(
        self,
        db: Session,
        new_members: List[Tuple[UUID, Role]],
        project_uuid: UUID,
        project_type: ProjectType = ProjectType.PROJECT,
    ) -> Sequence[ProjectMember]:
        current_members = self.get_list_of_project_members(
            db, project_uuid=project_uuid, project_type=project_type
        )
        current_member_ids = [cm.member_id for cm in current_members]
        project_members = []
        for project_member in new_members:
            if project_member[0] not in current_member_ids:
                # Set project member role based on team member role
                project_members.append(
                    {
                        "member_id": project_member[0],
                        "role": project_member[1],
                        "project_type": project_type,
                        "project_uuid": project_uuid,
                    }
                )
        if len(project_members) > 0:
            with db as session:
                session.execute(insert(ProjectMember).values(project_members))
                session.commit()
        return self.get_list_of_project_members(
            db, project_uuid=project_uuid, project_type=project_type
        )

    def get_by_project_and_member_id(
        self,
        db: Session,
        project_uuid: UUID,
        member_id: UUID,
        project_type: ProjectType = ProjectType.PROJECT,
    ) -> ProjectMember | None:
        statement: Select = (
            select(ProjectMember, Bundle("user", User.id))
            .join(ProjectMember.member)
            .where(ProjectMember.project_uuid == project_uuid)
            .where(ProjectMember.project_type == project_type)
            .where(ProjectMember.member_id == member_id)
        )
        with db as session:
            project_member = session.execute(statement).one_or_none()
            if project_member:
                set_url_attr(project_member[0], project_member[1])
                return project_member[0]
        return None

    def get_list_of_project_members(
        self,
        db: Session,
        *,
        project_uuid: UUID,
        project_type: ProjectType = ProjectType.PROJECT,
        role: Optional[Role] = None,
    ) -> Sequence[ProjectMember]:
        statement: Select = (
            select(
                ProjectMember,
                Bundle("user", User.id, User.first_name, User.last_name, User.email),
            )
            .join(ProjectMember.member)
            .where(ProjectMember.project_uuid == project_uuid)
            .where(ProjectMember.project_type == project_type)
        )

        # Conditionally join the correct project relationship based on project_type
        if project_type == ProjectType.PROJECT:
            statement = statement.join(ProjectMember.uas_project).where(
                Project.is_active
            )
        elif project_type == ProjectType.INDOOR_PROJECT:
            statement = statement.join(ProjectMember.indoor_project).where(
                IndoorProject.is_active
            )

        if role:
            statement = statement.where(ProjectMember.role == role)
        project_members: list[ProjectMember] = []
        with db as session:
            results = session.execute(statement).all()
            for project_member in session.execute(statement).all():
                set_name_and_email_attr(project_member[0], project_member[1])
                set_url_attr(project_member[0], project_member[1])
                project_members.append(project_member[0])
        return project_members

    def update_project_member(
        self,
        db: Session,
        project_member_obj: ProjectMember,
        project_member_in: ProjectMemberUpdate,
    ) -> UpdateProjectMember:
        """Update project member role. Reject update action if:
        - The member being updated is the project creator.
        - The member being updated is the only owner of the project.
        Args:
            db (Session): Database session.
            project_member_obj (ProjectMember): Project member object.
            project_member_in (ProjectMemberUpdate): Project member update.

        Returns:
            UpdateProjectMember: Update project member response.
        """
        with db as session:
            # Merge project member obj into session
            project_member_obj = session.merge(project_member_obj)

            # Get project using the target_project property
            project = project_member_obj.target_project
            if not project:
                return {
                    "response_code": status.HTTP_404_NOT_FOUND,
                    "message": "Project not found",
                    "result": None,
                }

            # Check if project is active
            if hasattr(project, "is_active") and not project.is_active:
                return {
                    "response_code": status.HTTP_404_NOT_FOUND,
                    "message": "Project is not active",
                    "result": None,
                }

            # Get all project owners
            owners_statement = (
                select(ProjectMember)
                .where(ProjectMember.project_uuid == project_member_obj.project_uuid)
                .where(ProjectMember.project_type == project_member_obj.project_type)
                .where(ProjectMember.role == Role.OWNER)
            )
            project_owners = session.execute(owners_statement).scalars().all()
            # Reject update action if the member being updated is the project creator
            if project_member_obj.member_id == project.owner_id:
                return {
                    "response_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Cannot change project creator role",
                    "result": None,
                }
            # Reject update action if there is only one owner and its the member being updated
            if (
                len(project_owners) == 1
                and project_owners[0].id == project_member_obj.id
            ):
                return {
                    "response_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Must have at least one project owner",
                    "result": None,
                }
            # Update project member role
            updated_project_member = crud.project_member.update(
                db, db_obj=project_member_obj, obj_in=project_member_in
            )
            # Return success response
            return {
                "response_code": status.HTTP_200_OK,
                "message": "Project member updated",
                "result": updated_project_member,
            }

    def delete_multi(
        self,
        db: Session,
        project_uuid: UUID,
        team_id: UUID,
        project_type: ProjectType = ProjectType.PROJECT,
    ) -> Sequence[ProjectMember]:
        # Build the base statement
        statement = (
            select(ProjectMember)
            .where(ProjectMember.project_uuid == project_uuid)
            .where(ProjectMember.project_type == project_type)
            .where(ProjectMember.role != Role.OWNER)
        )

        # Conditionally join the correct project relationship based on project_type
        if project_type == ProjectType.PROJECT:
            statement = statement.join(ProjectMember.uas_project).where(
                Project.team_id == team_id
            )
        elif project_type == ProjectType.INDOOR_PROJECT:
            statement = statement.join(ProjectMember.indoor_project).where(
                IndoorProject.team_id == team_id
            )

        with db as session:
            project_members = session.scalars(statement).all()
            if len(project_members) > 0:
                for project_member in project_members:
                    session.delete(project_member)
                session.commit()
        return project_members


project_member = CRUDProjectMember(ProjectMember)
