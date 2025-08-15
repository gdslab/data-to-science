from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.models.project_type import ProjectType
from app.schemas.project_member import ProjectMemberCreate
from app.schemas.role import Role
from app.tests.utils.project import create_project
from app.tests.utils.indoor_project import create_indoor_project
from app.tests.utils.user import create_user


def create_project_member(
    db: Session,
    role: Role = Role.VIEWER,
    email: str | None = None,
    member_id: UUID | None = None,
    project_uuid: UUID | None = None,
    project_type: ProjectType = ProjectType.PROJECT,
) -> models.ProjectMember:
    if member_id is None and email is None:
        user = create_user(db)
        member_id = user.id
    if project_uuid is None:
        if project_type == ProjectType.PROJECT:
            project = create_project(db)
            project_uuid = project.id
        elif project_type == ProjectType.INDOOR_PROJECT:
            indoor_project = create_indoor_project(db)
            project_uuid = indoor_project.id
        else:
            raise ValueError(f"Unsupported project type: {project_type}")

    if member_id:
        project_member_in = ProjectMemberCreate(member_id=member_id)
    if email:
        project_member_in = ProjectMemberCreate(email=email, member_id=None)
    project_member_in.role = role

    # Create project member
    project_member = crud.project_member.create_with_project(
        db,
        obj_in=project_member_in,
        project_uuid=project_uuid,
        project_type=project_type,
    )
    if project_member is None:
        raise ValueError("Failed to create project member")

    return project_member
