from sqlalchemy.orm import Session

from app import crud, schemas
from app.tests.utils.breedbase_connection import create_breedbase_connection
from app.tests.utils.project import create_project
from app.tests.conftest import pytest_requires_breedbase
from app.tests.utils.user import create_user


@pytest_requires_breedbase
def test_create_breedbase_connection(db: Session) -> None:
    # Create project
    project = create_project(db)

    # Fake base URL
    base_url = "https://example.com"

    # Fake study ID
    study_id = "1234567890"

    # Create breedbase connection schema
    breedbase_connection_in = schemas.BreedbaseConnectionCreate(
        base_url=base_url,
        study_id=study_id,
    )

    # Create breedbase connection in database
    breedbase_connection = crud.breedbase_connection.create_with_project(
        db, obj_in=breedbase_connection_in, project_id=project.id
    )

    # Verify that the breedbase connection was created
    assert breedbase_connection is not None
    assert breedbase_connection.project_id == project.id
    assert breedbase_connection.study_id == study_id


@pytest_requires_breedbase
def test_read_breedbase_connection(db: Session) -> None:
    # Create project
    project = create_project(db)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # Get breedbase connection from database
    breedbase_connection_from_db = crud.breedbase_connection.get(
        db, id=breedbase_connection.id
    )

    # Verify that the breedbase connection was created
    assert breedbase_connection_from_db is not None
    assert breedbase_connection_from_db.project_id == project.id
    assert breedbase_connection_from_db.study_id == breedbase_connection.study_id
    assert breedbase_connection_from_db.base_url == breedbase_connection.base_url


@pytest_requires_breedbase
def test_read_breedbase_connections(db: Session) -> None:
    # Create project
    project = create_project(db)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # Create another breedbase connection
    breedbase_connection_2 = create_breedbase_connection(db, project.id)

    # Get breedbase connections from database
    breedbase_connections_from_db = crud.breedbase_connection.get_multi_by_project_id(
        db, project_id=project.id
    )

    # Verify that the breedbase connections were created
    assert len(breedbase_connections_from_db) == 2
    assert breedbase_connection.id in [
        connection.id for connection in breedbase_connections_from_db
    ]
    assert breedbase_connection_2.id in [
        connection.id for connection in breedbase_connections_from_db
    ]


@pytest_requires_breedbase
def test_get_breedbase_connection_by_study_id(db: Session) -> None:
    # Create project
    project = create_project(db)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # Get breedbase connection from database
    breedbase_connections = crud.breedbase_connection.get_by_study_id(
        db, study_id=breedbase_connection.study_id, user_id=project.owner_id
    )

    # Verify that the breedbase connection was found
    assert len(breedbase_connections) == 1
    assert breedbase_connections[0].project_id == project.id
    assert breedbase_connections[0].study_id == breedbase_connection.study_id
    assert breedbase_connections[0].base_url == breedbase_connection.base_url

    # Create another project with the same study_id
    project2 = create_project(db, owner_id=project.owner_id)
    breedbase_connection2 = create_breedbase_connection(
        db, project2.id, study_id=breedbase_connection.study_id
    )

    # Get all breedbase connections for the study_id
    breedbase_connections = crud.breedbase_connection.get_by_study_id(
        db, study_id=breedbase_connection.study_id, user_id=project.owner_id
    )

    # Verify that both connections were found
    assert len(breedbase_connections) == 2
    connection_ids = [conn.id for conn in breedbase_connections]
    assert breedbase_connection.id in connection_ids
    assert breedbase_connection2.id in connection_ids

    # Test with a different user who doesn't have access
    other_user = create_user(db)
    breedbase_connections = crud.breedbase_connection.get_by_study_id(
        db, study_id=breedbase_connection.study_id, user_id=other_user.id
    )

    # Verify that no connections are returned for user without access
    assert len(breedbase_connections) == 0


@pytest_requires_breedbase
def test_update_breedbase_connection(db: Session) -> None:
    # Create project
    project = create_project(db)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # New study ID
    new_study_id = "1111111111"

    # Update breedbase connection
    breedbase_connection_in = schemas.BreedbaseConnectionUpdate(
        base_url="https://example.com",
        study_id=new_study_id,
    )

    # Update breedbase connection in database
    breedbase_connection_updated = crud.breedbase_connection.update(
        db, db_obj=breedbase_connection, obj_in=breedbase_connection_in
    )

    # Verify that the breedbase connection was updated
    assert breedbase_connection_updated is not None
    assert breedbase_connection_updated.project_id == project.id
    assert breedbase_connection_updated.study_id == new_study_id


@pytest_requires_breedbase
def test_remove_breedbase_connection(db: Session) -> None:
    # Create project
    project = create_project(db)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # Remove breedbase connection from database
    removed_breedbase_connection = crud.breedbase_connection.remove(
        db, id=breedbase_connection.id
    )

    # Verify that the breedbase connection was removed
    assert removed_breedbase_connection is not None
    assert removed_breedbase_connection.id == breedbase_connection.id
    assert removed_breedbase_connection.project_id == project.id
    assert removed_breedbase_connection.study_id == breedbase_connection.study_id

    # Get breedbase connection from database
    breedbase_connection_from_db = crud.breedbase_connection.get(
        db, id=breedbase_connection.id
    )

    # Verify that the breedbase connection was removed
    assert breedbase_connection_from_db is None
