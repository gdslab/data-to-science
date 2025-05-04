from datetime import date
import logging
import json
from typing import List, Optional, Sequence, Tuple, TypedDict
from uuid import UUID

from fastapi import status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import joinedload, Session

from app import crud
from app.crud.base import CRUDBase
from app.models.data_product import DataProduct
from app.models.file_permission import FilePermission
from app.models.flight import Flight
from app.models.location import Location
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.team_member import TeamMember
from app.models.user import User
from app.models.utils.utcnow import utcnow
from app.schemas.project import (
    Centroid,
    ProjectCreate,
    ProjectUpdate,
    Project as ProjectSchema,
    Projects,
)
from app.schemas.role import Role


logger = logging.getLogger("__name__")


class ReadProject(TypedDict):
    response_code: int
    message: str
    result: ProjectSchema | None


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def create_with_owner(
        self,
        db: Session,
        obj_in: ProjectCreate,
        owner_id: UUID,
    ) -> ReadProject:
        """Create new project and add user as project member."""
        obj_in_data = jsonable_encoder(obj_in)
        # Check if team was included and if user has the team member "owner" role
        team_members: Sequence[TeamMember] = []
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
            if not is_team_owner(owner_id, team_members, include_manager=True):
                return {
                    "response_code": status.HTTP_403_FORBIDDEN,
                    "message": 'Only team member with "owner" or "manager" role can perform this action',
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
            member_id=owner_id, project_id=project_db_obj.id, role=Role.OWNER
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
                            role=team_member.role,
                        )
                    )
            if len(project_members) > 0:
                with db as session:
                    session.add_all(project_members)
                    session.commit()

        try:
            project_schema = ProjectSchema.model_validate(project_db_obj)
        except Exception as e:
            logger.error(e)
            return {
                "response_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred while creating project",
                "result": None,
            }

        return {
            "response_code": status.HTTP_201_CREATED,
            "message": "Project created successfully",
            "result": project_schema,
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
                if (permission == "rwd" and member_role != Role.OWNER) or (
                    permission == "rw"
                    and (member_role != Role.OWNER and member_role != Role.MANAGER)
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
    ) -> List[Projects]:
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
                setattr(project_obj, "centroid", Centroid(x=center_x, y=center_y))
                # count of project's active flights and most recent flight date
                flight_count, most_recent_flight = (
                    get_flight_count_and_most_recent_flight(project_obj)
                )
                setattr(project_obj, "flight_count", flight_count)
                setattr(project_obj, "most_recent_flight", most_recent_flight)
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
    ) -> ReadProject:
        """Update project and add team members as project members if a new team is being added.

        Args:
            db (Session): Database session.
            project_id (UUID): ID of project to update.
            project_obj (Project): Project object to update
            project_in (ProjectUpdate): Project update object
            user_id (UUID): ID of user updating project

        Returns:
            ReadProject: ReadProject object containing response code, message, and updated project.
        """
        project_in_data = jsonable_encoder(project_in)
        # Only process team changes if a new team_id is provided and it's different from current
        if (
            project_in_data.get("team_id") is not None
            and project_obj.team_id != project_in_data["team_id"]
        ):
            team_members = crud.team_member.get_list_of_team_members(
                db, team_id=project_in_data["team_id"]
            )
            # Check permissions
            if len(team_members) == 0 or not is_team_owner(
                user_id, team_members, include_manager=True
            ):
                return {
                    "response_code": status.HTTP_403_FORBIDDEN,
                    "message": "Only team owner can perform this action",
                    "result": None,
                }

            # Add team members as project members
            crud.project_member.create_multi_with_project(
                db,
                new_members=[
                    (team_member.member_id, team_member.role)
                    for team_member in team_members
                ],
                project_id=project_id,
            )

        # Finish updating project
        updated_project = crud.project.update(db, db_obj=project_obj, obj_in=project_in)
        try:
            # Get project role for user updating project
            project_member = crud.project_member.get_by_project_and_member_id(
                db, project_id=project_id, member_id=user_id
            )
            if project_member:
                setattr(updated_project, "role", project_member.role)
            else:
                setattr(updated_project, "role", "viewer")
            # Validate and return updated project
            updated_project_schema = ProjectSchema.model_validate(updated_project)
        except Exception as e:
            logger.error(e)
            return {
                "response_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred while updating project",
                "result": None,
            }
        return {
            "response_code": status.HTTP_200_OK,
            "message": "Project updated successfully",
            "result": updated_project_schema,
        }

    def update_project_visibility(
        self, db: Session, project_id: UUID, is_public: bool = True
    ) -> Optional[Project]:
        """
        Updates the project's publication status and the visibility of all its data products.

        Args:
            db (Session): Database session.
            project_id (UUID): ID of project to update.
            is_public (bool): Whether to make the project and its data products public (True)
                             or private (False).

        Returns:
            Project: Updated project object.
        """
        with db as session:
            # Update the file permissions for each data product in the project
            file_permission_ids_subquery = (
                select(FilePermission.id)
                .join(DataProduct)
                .join(Flight)
                .join(Project)
                .where(Project.id == project_id)
                .where(Project.is_active)
                .where(Flight.is_active)
                .where(DataProduct.is_active)
                .scalar_subquery()
            )

            update_file_permissions_sql = (
                update(FilePermission)
                .where(FilePermission.id.in_(file_permission_ids_subquery))
                .values(is_public=is_public)
            )

            # Update the project publication status
            update_project_sql = (
                update(Project)
                .where(Project.id == project_id)
                .where(Project.is_active)
                .values(is_published=is_public)
            )

            # Execute the update queries
            session.execute(update_file_permissions_sql)
            session.execute(update_project_sql)

            # Commit the changes
            session.commit()

            # Return the updated project
            return self.get(db, project_id)

    def deactivate(
        self, db: Session, project_id: UUID, user_id: UUID
    ) -> Optional[Project]:
        """Deactivate project and associated flights."""
        with db as session:
            # Update project to be inactive
            update_project_sql = (
                update(Project)
                .where(and_(Project.id == project_id, Project.owner_id == user_id))
                .values(is_active=False, deactivated_at=utcnow())
            )
            session.execute(update_project_sql)
            session.commit()

            # Get deactivated project
            get_project_sql = (
                select(Project)
                .options(joinedload(Project.flights))
                .where(Project.id == project_id, Project.owner_id == user_id)
            )
            deactivated_project = session.execute(get_project_sql).scalar()

        # Deactivate flights associated with project
        if deactivated_project:
            if len(deactivated_project.flights) > 0:
                for flight in deactivated_project.flights:
                    crud.flight.deactivate(db, flight_id=flight.id)

        # Add owner role to deactivated project (necessary for validation)
        setattr(deactivated_project, "role", "owner")

        return deactivated_project


def get_flight_count_and_most_recent_flight(
    project: Project,
) -> Tuple[int, Optional[date]]:
    """Calculate total number of active flights in a project and
    find date for most recent flight.

    Args:
        project (Project): Project with flights.

    Returns:
        Tuple[int, Optional[date]]: Number of flights in project and date of most recent flight.
    """
    flight_count = 0
    most_recent_flight = None

    for flight in project.flights:
        if flight.is_active:
            if most_recent_flight:
                if most_recent_flight < flight.acquisition_date:
                    most_recent_flight = flight.acquisition_date
            else:
                most_recent_flight = flight.acquisition_date
            flight_count += 1

    return flight_count, most_recent_flight


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


def is_team_owner(
    user_id: UUID, team_members: Sequence[TeamMember], include_manager: bool = False
) -> bool:
    """Returns True if user_id matches a user on a team and is the team owner.

    Args:
        user_id (UUID): User ID to check for on a team.
        team_members (Sequence[TeamMember]): List of team members.
        include_manager (bool): Whether to include manager role in check.
    Returns:
        bool: True if the user ID matches a user in the team member list and is the team owner,
        otherwise False.
    """
    for team_member in team_members:
        if team_member.member_id == user_id and team_member.role == Role.OWNER:
            return True
        if (
            include_manager
            and team_member.member_id == user_id
            and team_member.role == Role.MANAGER
        ):
            return True
    return False


project = CRUDProject(Project)
