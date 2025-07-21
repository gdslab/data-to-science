from typing import List, Optional, Sequence, Tuple, TypedDict
from uuid import UUID

from fastapi import status
from sqlalchemy import select, true
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Bundle, Session, joinedload
from sqlalchemy.sql.selectable import Select

from app import crud
from app.crud.base import CRUDBase
from app.crud.crud_team_member import set_name_and_email_attr, set_url_attr
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
        project_id: UUID,
        project_type: ProjectType = ProjectType.PROJECT
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

        # Query project by id
        with db as session:
            project = crud.project.get(db, id=project_id)
            if not project:
                return None

        # Check if user is project owner
        is_project_owner = project.owner_id == user_obj.id

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
                project_id=project_id,
                project_type=project_type,
                project_uuid=project_id,
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
        project_id: UUID,
        project_type: ProjectType = ProjectType.PROJECT,
    ) -> Sequence[ProjectMember]:
        current_members = self.get_list_of_project_members(db, project_id=project_id)
        current_member_ids = [cm.member_id for cm in current_members]
        project_members = []
        for project_member in new_members:
            if project_member[0] not in current_member_ids:
                # Set project member role based on team member role
                project_members.append(
                    {
                        "member_id": project_member[0],
                        "role": project_member[1],
                        "project_id": project_id,
                        "project_type": project_type,
                        "project_uuid": project_id,
                    }
                )
        if len(project_members) > 0:
            with db as session:
                session.execute(insert(ProjectMember).values(project_members))
                session.commit()
        return self.get_list_of_project_members(db, project_id=project_id)

    def get_by_project_and_member_id(
        self, db: Session, project_id: UUID, member_id: UUID
    ) -> ProjectMember | None:
        statement: Select = (
            select(ProjectMember, Bundle("user", User.id))
            .join(ProjectMember.member)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.member_id == member_id)
        )
        with db as session:
            project_member = session.execute(statement).one_or_none()
            if project_member:
                set_url_attr(project_member[0], project_member[1])
                return project_member[0]
        return None

    def get_list_of_project_members(
        self, db: Session, *, project_id: UUID, role: Optional[Role] = None
    ) -> Sequence[ProjectMember]:
        statement: Select = (
            select(
                ProjectMember,
                Bundle("user", User.id, User.first_name, User.last_name, User.email),
            )
            .join(ProjectMember.project)
            .join(ProjectMember.member)
            .where(ProjectMember.project_id == project_id)
            .where(Project.is_active)
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

            # Get project
            project_statement = (
                select(Project)
                .where(Project.id == project_member_obj.project_id)
                .where(Project.is_active == true())
            )
            project = session.execute(project_statement).scalar_one_or_none()
            if not project:
                return {
                    "response_code": status.HTTP_404_NOT_FOUND,
                    "message": "Project not found",
                    "result": None,
                }

            # Get all project owners
            owners_statement = (
                select(ProjectMember)
                .where(ProjectMember.project_id == project.id)
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
        self, db: Session, project_id: UUID, team_id: UUID
    ) -> Sequence[ProjectMember]:
        statement = (
            select(ProjectMember)
            .join(Project)
            .join(Team)
            .where(Project.id == project_id)
            .where(Team.id == team_id)
            .where(ProjectMember.role != Role.OWNER)
        )
        with db as session:
            project_members = session.scalars(statement).all()
            if len(project_members) > 0:
                for project_member in project_members:
                    session.delete(project_member)
                session.commit()
        return project_members


project_member = CRUDProjectMember(ProjectMember)
