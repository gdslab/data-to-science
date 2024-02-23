import logging
import json
from typing import Sequence, TypedDict
from uuid import UUID

from fastapi import status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select, update, or_
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import joinedload, Session

from app import crud, models, schemas
from app.crud.base import CRUDBase
from app.models.data_product import DataProduct
from app.models.flight import Flight
from app.models.location import Location
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.team_member import TeamMember
from app.models.utils.user import utcnow
from app.schemas.project import ProjectCreate, ProjectUpdate


logger = logging.getLogger("__name__")


def is_team_member(user_id: UUID, team_members: Sequence[TeamMember]) -> bool:
    """Returns True if user_id matches a user on a team.

    Args:
        user_id (UUID): User ID to check for on a team.
        team_members (Sequence[TeamMember]): List of team members.

    Returns:
        bool: True if the user ID matches a user in the team member list, otherwise False.
    """
    for team_member in team_members:
        if team_member.member_id == user_id:
            return True
    return False


class ReadProject(TypedDict):
    response_code: int
    message: str
    result: Project | None


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def create_with_owner(
        self,
        db: Session,
        obj_in: ProjectCreate,
        owner_id: UUID,
    ) -> ReadProject:
        """Create new project and add user as project member."""
        obj_in_data = jsonable_encoder(obj_in)
        # check if team was included and if user is team member
        team_members = []
        if obj_in_data.get("team_id"):
            team_members = crud.team_member.get_list_of_team_members(
                db, team_id=obj_in_data.get("team_id")
            )
            if len(team_members) < 1:
                return {
                    "response_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Team does not have any members",
                    "result": None,
                }
            if not is_team_member(owner_id, team_members):
                return {
                    "response_code": status.HTTP_403_FORBIDDEN,
                    "message": "Only team member can perform this action",
                    "result": None,
                }
        # add location to db
        location_db_obj = models.Location(**jsonable_encoder(obj_in_data["location"]))
        with db as session:
            session.add(location_db_obj)
            session.commit()
            session.refresh(location_db_obj)
        # remove location from project object and add location id
        del obj_in_data["location"]
        obj_in_data["location_id"] = location_db_obj.id
        # add project to db
        project_db_obj = self.model(**obj_in_data, owner_id=owner_id)
        with db as session:
            session.add(project_db_obj)
            session.commit()
            session.refresh(project_db_obj)
        # add project memebers to db
        member_db_obj = ProjectMember(
            member_id=owner_id, project_id=project_db_obj.id, role="owner"
        )
        with db as session:
            session.add(member_db_obj)
            session.commit()
            session.refresh(member_db_obj)
        # add team members as project members
        if len(team_members) > 0:
            project_members = []
            for team_member in team_members:
                if team_member.member_id != owner_id:
                    project_members.append(
                        ProjectMember(
                            member_id=team_member.member_id,
                            project_id=project_db_obj.id,
                            role="viewer",
                        )
                    )
            if len(project_members) > 0:
                with db as session:
                    session.add_all(project_members)
                    session.commit()

        return {
            "response_code": status.HTTP_201_CREATED,
            "message": "Project created successfully",
            "result": project_db_obj,
        }

    def get_user_project(
        self, db: Session, user_id: UUID, project_id: UUID, permission: str = "r"
    ) -> ReadProject:
        """Retrieve project by id."""
        # Selects project by id if user is project member
        query_by_project_member = (
            select(Project, func.ST_AsGeoJSON(Location), ProjectMember)
            .join(Project.location)
            .join(Project.members)
            .where(Project.id == project_id)
            .where(Project.is_active)
            .where(ProjectMember.member_id == user_id)
        )
        with db as session:
            try:
                project = session.execute(query_by_project_member).one_or_none()
            except MultipleResultsFound as e:
                logger.error(e)
                return {
                    "response_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "Error occurred while fetching project",
                    "result": None,
                }
            if project and len(project) == 3:
                member_role = project[2].role
                if (permission == "rwd" and member_role != "owner") or (
                    permission == "rw"
                    and (member_role != "owner" and member_role != "manager")
                ):
                    return {
                        "response_code": status.HTTP_403_FORBIDDEN,
                        "message": "Permission denied",
                        "result": None,
                    }
                setattr(
                    project[0],
                    "is_owner",
                    user_id == project[0].owner_id or member_role == "owner",
                )
                setattr(project[0], "field", json.loads(project[1]))
                flight_count = 0
                for flight in project[0].flights:
                    if flight.is_active:
                        flight_count += 1
                setattr(project[0], "flight_count", flight_count)
                return {
                    "response_code": status.HTTP_200_OK,
                    "message": "Project fetched successfully",
                    "result": project[0],
                }
            else:
                return {
                    "response_code": status.HTTP_404_NOT_FOUND,
                    "message": "Project not found",
                    "result": None,
                }

    def get_user_project_list(
        self,
        db: Session,
        user_id: UUID,
        edit_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Project]:
        """List of projects the user belongs to."""
        # project member
        if edit_only:
            query_by_project_member = (
                select(Project, func.ST_AsGeoJSON(Location), ProjectMember)
                .join(Project.location)
                .join(Project.members)
                .where(Project.is_active)
                .where(ProjectMember.member_id == user_id)
                .where(
                    or_(ProjectMember.role == "manager", ProjectMember.role == "owner")
                )
            )
        else:
            query_by_project_member = (
                select(Project, func.ST_AsGeoJSON(Location), ProjectMember)
                .join(Project.location)
                .join(Project.members)
                .where(Project.is_active)
                .where(ProjectMember.member_id == user_id)
            )
        with db as session:
            projects = session.execute(query_by_project_member).all()
            final_projects = []
            # indicate if project member is also project owner
            for project in projects:
                setattr(
                    project[0],
                    "is_owner",
                    user_id == project[0].owner_id or project[2].role == "owner",
                )
                setattr(project[0], "field", json.loads(project[1]))
                flight_count = 0
                for flight in project[0].flights:
                    if flight.is_active:
                        flight_count += 1
                setattr(project[0], "flight_count", flight_count)
                final_projects.append(project[0])
        return final_projects

    def update_project(
        self,
        db: Session,
        project_id: UUID,
        project_obj: Project,
        project_in: ProjectUpdate,
        user_id: UUID,
    ):
        project_in_data = jsonable_encoder(project_in)
        # if team association is being updated, check that user has team permission
        if (
            project_in_data.get("team_id") is not None
            and project_obj.team_id != project_in_data["team_id"]
        ):
            team_members = crud.team_member.get_list_of_team_members(
                db, team_id=project_in_data["team_id"]
            )
            if len(team_members) == 0 or not is_team_member(user_id, team_members):
                return {
                    "response_code": status.HTTP_403_FORBIDDEN,
                    "message": "Only team owner can perform this action",
                    "result": None,
                }
        # replacing current team with new team
        if project_obj.team_id and project_in_data.get("team_id") is not None:
            # remove current team's project members
            crud.project_member.delete_multi(
                db, project_id=project_id, team_id=project_obj.team_id
            )
            # add new team's project members
            team_members = crud.team_member.get_list_of_team_members(
                db, team_id=project_in_data["team_id"]
            )
            if len(team_members) > 0:
                team_member_ids = [
                    team_member.member_id for team_member in team_members
                ]
                crud.project_member.create_multi_with_project(
                    db, member_ids=team_member_ids, project_id=project_id
                )
        # adding new team
        if not project_obj.team_id and project_in_data.get("team_id") is not None:
            # add new team's project members
            team_members = crud.team_member.get_list_of_team_members(
                db, team_id=project_in_data["team_id"]
            )
            if len(team_members) > 0:
                team_member_ids = [
                    team_member.member_id for team_member in team_members
                ]
                crud.project_member.create_multi_with_project(
                    db, member_ids=team_member_ids, project_id=project_id
                )
        # dropping current team
        if project_obj.team_id and project_in_data.get("team_id") is None:
            # remove current team's project members
            crud.project_member.delete_multi(
                db, project_id=project_id, team_id=project_obj.team_id
            )

        # finish updating project
        updated_project = crud.project.update(db, db_obj=project_obj, obj_in=project_in)
        return {
            "response_code": status.HTTP_200_OK,
            "message": "Project updated successfully",
            "result": updated_project,
        }

    def deactivate(self, db: Session, project_id: UUID) -> Project | None:
        update_project_sql = (
            update(Project)
            .where(Project.id == project_id)
            .values(is_active=False, deactivated_at=utcnow())
        )
        with db as session:
            session.execute(update_project_sql)
            session.commit()

        get_project_sql = (
            select(Project)
            .options(joinedload(Project.flights))
            .where(Project.id == project_id)
        )
        with db as session:
            deactivated_project = session.execute(get_project_sql).scalar()

        if deactivated_project and len(deactivated_project.flights) > 0:
            for flight in deactivated_project.flights:
                with db as session:
                    crud.flight.deactivate(db, flight_id=flight.id)

        return deactivated_project


project = CRUDProject(Project)
