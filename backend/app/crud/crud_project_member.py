from typing import List, Sequence, Tuple, TypedDict
from uuid import UUID

from fastapi import status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Bundle, Session
from sqlalchemy.sql.selectable import Select

from app import crud
from app.crud.base import CRUDBase
from app.crud.crud_team_member import set_name_and_email_attr, set_url_attr
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.team import Team
from app.models.team_member import TeamMember
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
        self, db: Session, *, obj_in: ProjectMemberCreate, project_id: UUID
    ) -> ProjectMember | None:
        obj_in_data = jsonable_encoder(obj_in)
        if "email" in obj_in_data and obj_in_data.get("email"):
            statement = select(User).filter_by(email=obj_in_data.get("email"))
            with db as session:
                user_obj = session.scalars(statement).one_or_none()
                if user_obj:
                    db_obj = self.model(
                        role=obj_in_data.get("role", "viewer"),
                        member_id=user_obj.id,
                        project_id=project_id,
                    )
                    session.add(db_obj)
                    session.commit()
                    session.refresh(db_obj)
                else:
                    db_obj = None
        elif "member_id" in obj_in_data:
            with db as session:
                db_obj = self.model(
                    member_id=obj_in_data.get("member_id"),
                    role=obj_in_data.get("role", "viewer"),
                    project_id=project_id,
                )
                session.add(db_obj)
                session.commit()
                session.refresh(db_obj)
        return db_obj

    def create_multi_with_project(
        self, db: Session, new_members: List[Tuple[UUID, Role]], project_id: UUID
    ) -> Sequence[ProjectMember]:
        current_members = self.get_list_of_project_members(db, project_id=project_id)
        current_member_ids = [cm.member_id for cm in current_members]
        project_members = []
        for project_member in new_members:
            if project_member[0] not in current_member_ids:
                # Set project member role based on team member role
                if project_member[1] == Role.OWNER:
                    project_member_role = "owner"
                else:
                    project_member_role = "viewer"
                project_members.append(
                    {
                        "member_id": project_member[0],
                        "role": project_member_role,
                        "project_id": project_id,
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
        self, db: Session, *, project_id: UUID, role: str = ""
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
        # only update if there will still be at least one owner for the project
        project_owners = self.get_list_of_project_members(
            db, project_id=project_member_obj.project_id, role="owner"
        )
        # deny update action if there is only one owner and its the member being updated
        if len(project_owners) == 1 and project_owners[0].id == project_member_obj.id:
            return {
                "response_code": status.HTTP_400_BAD_REQUEST,
                "message": "Must have at least one project owner",
                "result": None,
            }
        updated_project_member = crud.project_member.update(
            db, db_obj=project_member_obj, obj_in=project_member_in
        )
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
            .where(ProjectMember.role != "owner")
        )
        with db as session:
            project_members = session.scalars(statement).all()
            if len(project_members) > 0:
                for project_member in project_members:
                    session.delete(project_member)
                session.commit()
        return project_members


project_member = CRUDProjectMember(ProjectMember)
