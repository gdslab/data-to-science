from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.project_member import ProjectMemberCreate
from app.tests.utils.project import create_random_project
from app.tests.utils.user import create_random_user


def create_random_project_member(
    db: Session,
    member_id: UUID | None = None,
    project_id: UUID | None = None,
) -> models.ProjectMember:
    if member_id is None:
        user = create_random_user(db)
        member_id = user.id
    if project_id is None:
        project = create_random_project(db)
        project_id = project.id
    project_member_in = ProjectMemberCreate()
    return crud.project_member.create_with_project(
        db, obj_in=project_member_in, member_id=member_id, project_id=project_id
    )
