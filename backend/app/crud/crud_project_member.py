from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.team import Team
from app.models.user import User
from app.schemas.project_member import ProjectMemberCreate, ProjectMemberUpdate


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
        self, db: Session, member_ids: [UUID], project_id: UUID
    ) -> Sequence[ProjectMember]:
        project_members = []
        for member_id in member_ids:
            project_members.append(
                {"member_id": member_id, "role": "viewer", "project_id": project_id}
            )
        with db as session:
            session.execute(
                insert(ProjectMember).values(project_members).on_conflict_do_nothing()
            )
            session.commit()
        return self.get_list_of_project_members(db, project_id=project_id)

    def get_by_project_and_member_id(
        self, db: Session, project_id: UUID, member_id: UUID
    ) -> ProjectMember | None:
        statement = (
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.member_id == member_id)
        )
        with db as session:
            return session.scalar(statement)

    def get_list_of_project_members(
        self, db: Session, *, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[ProjectMember]:
        statement = (
            select(ProjectMember)
            .join(Project)
            .where(ProjectMember.project_id == project_id)
            .where(Project.is_active)
        )
        with db as session:
            return session.scalars(statement).all()

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
