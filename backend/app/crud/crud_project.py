import logging
import json
from typing import List, Sequence, TypedDict
from uuid import UUID

from fastapi import status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, select, update, or_
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import joinedload, Session

from app import crud
from app.crud.base import CRUDBase
from app.models.data_product import DataProduct
from app.models.flight import Flight
from app.models.location import Location
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.team_member import TeamMember
from app.models.user import User
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
        feature = obj_in_data["location"]
        # Get geometry from GeoJSON Feature (not interested in props)
        geometry = feature["geometry"]
        # Serialize geometry for ST_GeomFromGeoJSON function
        geom = func.ST_Force2D(func.ST_GeomFromGeoJSON(json.dumps(geometry)))
        location_db_obj = Location(geom=geom)
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
        # add role attribute
        setattr(project_db_obj, "role", "owner")
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
            select(
                Project,
                ProjectMember,
                func.ST_AsGeoJSON(Location),
                func.ST_X(func.ST_Centroid(Location.geom)).label("center_x"),
                func.ST_Y(func.ST_Centroid(Location.geom)).label("center_y"),
            )
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
            if project and len(project) == 5:
                member_role = project[1].role
                if (permission == "rwd" and member_role != "owner") or (
                    permission == "rw"
                    and (member_role != "owner" and member_role != "manager")
                ):
                    return {
                        "response_code": status.HTTP_403_FORBIDDEN,
                        "message": "Permission denied",
                        "result": None,
                    }
                setattr(project[0], "role", member_role)
                field_dict = json.loads(project[2])
                field_dict["properties"].update(
                    {"center_x": project[3], "center_y": project[4]}
                )
                setattr(project[0], "field", field_dict)
                flight_count = 0
                most_recent_flight = None
                for flight in project[0].flights:
                    if flight.is_active:
                        if most_recent_flight:
                            if most_recent_flight < flight.acquisition_date:
                                most_recent_flight = flight.acquisition_date
                        else:
                            most_recent_flight = flight.acquisition_date
                        flight_count += 1
                setattr(project[0], "flight_count", flight_count)
                setattr(project[0], "most_recent_flight", most_recent_flight)
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

    def get_user_projects(
        self,
        db: Session,
        user: User,
        has_raster: bool = False,
        include_all: bool = False,
    ) -> List[Project]:
        # query to select active projects associated with user
        if include_all and user.is_superuser:
            statement = (
                select(
                    Project,
                    func.ST_X(func.ST_Centroid(Location.geom)).label("center_x"),
                    func.ST_Y(func.ST_Centroid(Location.geom)).label("center_y"),
                )
                .join(Project.location)
                .where(Project.is_active)
            )
        else:
            statement = (
                select(
                    Project,
                    ProjectMember,
                    func.ST_X(func.ST_Centroid(Location.geom)).label("center_x"),
                    func.ST_Y(func.ST_Centroid(Location.geom)).label("center_y"),
                )
                .join(Project.members)
                .join(Project.location)
                .where(and_(Project.is_active, ProjectMember.member_id == user.id))
            )
        with db as session:
            final_projects = []
            # iterate over each returned project
            for project in session.execute(statement).all():
                # unpack project
                if include_all and user.is_superuser:
                    project_obj, center_x, center_y = project
                else:
                    project_obj, member_obj, center_x, center_y = project
                # add center x, y attributes to project obj
                setattr(project_obj, "centroid", {"x": center_x, "y": center_y})
                # count of project's active flights
                flight_count = get_flight_count(project_obj)
                setattr(project_obj, "flight_count", flight_count)
                # add project member role
                if include_all and user.is_superuser:
                    setattr(project_obj, "role", "owner")
                else:
                    setattr(project_obj, "role", member_obj.role)
                # add updated project obj to final list
                if not has_raster or (
                    has_raster and has_flight_with_raster_data_project(project_obj)
                ):
                    final_projects.append(project_obj)

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

        # finish updating project
        updated_project = crud.project.update(db, db_obj=project_obj, obj_in=project_in)
        return {
            "response_code": status.HTTP_200_OK,
            "message": "Project updated successfully",
            "result": updated_project,
        }

    def deactivate(
        self, db: Session, project_id: UUID, user_id: UUID
    ) -> Project | None:
        # update project's active status
        update_project_sql = (
            update(Project)
            .where(and_(Project.id == project_id, Project.owner_id == user_id))
            .values(is_active=False, deactivated_at=utcnow())
        )
        with db as session:
            session.execute(update_project_sql)
            session.commit()

        # get deactivated project that will be deactivated
        get_project_sql = (
            select(Project)
            .options(joinedload(Project.flights))
            .where(Project.id == project_id, Project.owner_id == user_id)
        )
        with db as session:
            deactivated_project = session.execute(get_project_sql).scalar()

        # deactivate flights associated with project
        if deactivated_project:
            if len(deactivated_project.flights) > 0:
                for flight in deactivated_project.flights:
                    with db as session:
                        crud.flight.deactivate(db, flight_id=flight.id)

            # add owner role to deactivated project
            setattr(deactivated_project, "role", "owner")

            return deactivated_project


def get_flight_count(project: Project) -> int:
    """Calculate total number of active flights in a project.

    Args:
        project (Project): Project with flights.

    Returns:
        int: Number of flights in project.
    """
    flight_count = 0

    for flight in project.flights:
        if flight.is_active:
            flight_count += 1

    return flight_count


def has_flight_with_raster_data_project(project: Project) -> bool:
    """Checks if a project has at least one active flight with one active data product.

    Args:
        project (Project): Project with flights.

    Returns:
        bool: True if project has raster data product, False if it doesn't.
    """
    has_at_least_one_raster_data_product = False

    for flight in project.flights:
        if flight.is_active:
            for data_product in flight.data_products:
                if data_product.data_type != "point_cloud" and data_product.is_active:
                    has_at_least_one_raster_data_product = True

    return has_at_least_one_raster_data_product


project = CRUDProject(Project)
