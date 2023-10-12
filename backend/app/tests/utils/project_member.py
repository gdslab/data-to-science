from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.project_member import ProjectMemberCreate
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user


def create_project_member(
    db: Session,
    email: str | None = None,
    member_id: UUID | None = None,
    project_id: UUID | None = None,
) -> models.ProjectMember:
    if member_id is None and email is None:
        user = create_user(db)
        member_id = user.id
    if project_id is None:
        project = create_project(db)
        project_id = project.id

    if member_id:
        project_member_in = ProjectMemberCreate(member_id=member_id)
    if email:
        project_member_in = ProjectMemberCreate(email=email, member_id=None)
    return crud.project_member.create_with_project(
        db, obj_in=project_member_in, project_id=project_id
    )
