from sqlalchemy.orm import Session

from app import crud, schemas
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user


def test_get_by_project_id_and_user_id(db: Session) -> None:
    """
    Test getting a project like by project ID and user ID.
    """
    project_id = create_project(db).id
    user_id = create_user(db).id

    # Create a project like
    project_like_in = schemas.ProjectLikeCreate(
        project_id=project_id,
        user_id=user_id,
    )
    crud.project_like.create(db, obj_in=project_like_in)

    # Get the project like
    project_like = crud.project_like.get_by_project_id_and_user_id(
        db, project_id, user_id
    )

    # Verify the project like was created
    assert project_like is not None
    assert project_like.project_id == project_id
    assert project_like.user_id == user_id
