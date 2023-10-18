import json
from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.location import Location
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.utils.user import utcnow
from app.schemas.project import ProjectCreate, ProjectUpdate


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def create_with_owner(
        self,
        db: Session,
        obj_in: ProjectCreate,
        owner_id: UUID,
    ) -> Project:
        """Create new project and add user as project member."""
        # add project to db
        obj_in_data = jsonable_encoder(obj_in)
        project_db_obj = self.model(**obj_in_data, owner_id=owner_id)
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
        self, db: Session, user_id: UUID, project_id: UUID
    ) -> Project | None:
        """Retrieve project by id."""
        # Selects project by id if one of the below items is true
        # - User is project member
        # - User is team member in team associated with project
        query_by_project_member = (
            select(Project, func.ST_AsGeoJSON(Location))
            .join(Project.location)
            .join(Project.members)
            .where(Project.id == project_id)
            .where(Project.is_active)
            .where(ProjectMember.member_id == user_id)
        )
        query_by_team_member = (
            select(Project, func.ST_AsGeoJSON(Location))
            .join(Project.location)
            .join(Project.team)
            .join(Team.members)
            .where(Project.id == project_id)
            .where(Project.is_active)
            .where(Project.team_id == TeamMember.team_id)
            .where(TeamMember.member_id == user_id)
        )
        with db as session:
            project1 = session.execute(query_by_project_member).one_or_none()
            project2 = session.execute(query_by_team_member).one_or_none()
            projects = []
            if project1:
                setattr(project1[0], "is_owner", user_id == project1[0].owner_id)
                setattr(project1[0], "field", json.loads(project1[1]))
                setattr(project1[0], "flight_count", len(project1[0].flights))
                projects.append(project1[0])
            if project2:
                setattr(project2[0], "is_owner", user_id == project2[0].owner_id)
                setattr(project2[0], "field", json.loads(project2[1]))
                setattr(project2[0], "flight_count", len(project2[0].flights))
                projects.append(project2[0])
            if len(set(projects)) > 1 or len(projects) < 1:
                project = None
            else:
                project = list(set(projects))[0]
        return project

    def get_user_project_list(
        self, db: Session, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Project]:
        """List of projects the user belongs to."""
        # project member
        query_by_project_member = (
            select(Project, func.ST_AsGeoJSON(Location))
            .join(Project.location)
            .join(Project.members)
            .where(Project.is_active)
            .where(ProjectMember.member_id == user_id)
        )
        query_by_team_member = (
            select(Project, func.ST_AsGeoJSON(Location))
            .join(Project.location)
            .join(Project.team)
            .join(Team.members)
            .where(Project.is_active)
            .where(Project.team_id == TeamMember.team_id)
            .where(TeamMember.member_id == user_id)
        )
        # team member
        with db as session:
            projects1 = session.execute(query_by_project_member).all()
            projects2 = session.execute(query_by_team_member).all()
            projects = list(set(projects1 + projects2))
            final_projects = []
            # indicate if project member is also project owner
            for project in projects:
                setattr(project[0], "is_owner", user_id == project[0].owner_id)
                setattr(project[0], "field", json.loads(project[1]))
                setattr(project[0], "flight_count", len(project[0].flights))
                final_projects.append(project[0])
        return final_projects

    def deactivate(self, db: Session, project_id: UUID) -> Project | None:
        deactivate_project = (
            update(Project)
            .where(Project.id == project_id)
            .values(is_active=False, deactivated_at=utcnow())
        )
        with db as session:
            session.execute(deactivate_project)
            session.commit()
        return crud.project.get(db, id=project_id)


project = CRUDProject(Project)
