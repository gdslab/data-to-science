from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.team import Team
from app.models.team_member import TeamMember
from app.schemas.project import ProjectCreate, ProjectUpdate


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def create_with_owner(
        self,
        db: Session,
        *,
        obj_in: ProjectCreate,
        owner_id: UUID,
    ) -> Project:
        """Create new project and add user as project member."""
        # add project to db
        obj_in_data = jsonable_encoder(obj_in)
        project_db_obj = self.model(
            **obj_in_data,
            owner_id=owner_id,
        )
        with db as session:
            session.add(project_db_obj)
            session.commit()
            session.refresh(project_db_obj)
        # add project memeber to db
        member_db_obj = ProjectMember(member_id=owner_id, project_id=project_db_obj.id)
        with db as session:
            session.add(member_db_obj)
            session.commit()
            session.refresh(member_db_obj)
        return project_db_obj

    def get_user_project(
        self, db: Session, *, user_id: UUID, project_id: UUID
    ) -> Project | None:
        """Retrieve project by id."""
        # Selects project by id if one of the below items is true
        # - User is owner of the project or a project member
        # - Project associated with a team and user is a team member
        query_project_owner_and_members = (
            select(Project)
            .join(Project.members)
            .where(
                and_(
                    or_(
                        Project.owner_id == user_id, ProjectMember.member_id == user_id
                    ),
                    Project.id == project_id,
                )
            )
        )
        query_project_team_members = (
            select(Project)
            .join(Project.team)
            .join(Team.members)
            .where(
                and_(
                    Project.team_id == TeamMember.team_id,
                    TeamMember.member_id == user_id,
                    Project.id == project_id,
                )
            )
        )
        with db as session:
            project1 = session.scalars(query_project_owner_and_members).one_or_none()
            project2 = session.scalars(query_project_team_members).one_or_none()
            projects = []
            if project1:
                setattr(project1, "is_owner", user_id == project1.owner_id)
                projects.append(project1)
            if project2:
                setattr(project2, "is_owner", user_id == project2.owner_id)
                projects.append(project2)
            if len(set(projects)) > 1 or len(projects) < 1:
                project = None
            else:
                project = list(set(projects))[0]
        return project

    def get_user_project_list(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Project]:
        """List of projects the user belongs to."""
        # project member
        query_project_owner_and_members = (
            select(Project)
            .join(Project.members)
            .where(
                or_(Project.owner_id == user_id, ProjectMember.member_id == user_id),
            )
        )
        query_project_team_members = (
            select(Project)
            .join(Project.team)
            .join(Team.members)
            .where(
                and_(
                    Project.team_id == TeamMember.team_id,
                    TeamMember.member_id == user_id,
                ),
            )
        )
        # team member
        with db as session:
            projects1 = session.scalars(query_project_owner_and_members).all()
            projects2 = session.scalars(query_project_team_members).all()
            projects = list(set(list(projects1) + list(projects2)))
            # indicate if project member is also project owner
            for project in projects:
                setattr(project, "is_owner", user_id == project.owner_id)
        return projects


project = CRUDProject(Project)
