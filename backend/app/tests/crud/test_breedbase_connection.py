from sqlalchemy.orm import Session

from app import crud, schemas
from app.tests.utils.breedbase_connection import create_breedbase_connection
from app.tests.utils.project import create_project


def test_create_breedbase_connection(db: Session) -> None:
    # Create project
    project = create_project(db)

    # Fake base URL
    base_url = "https://example.com"

    # Fake trial ID
    trial_id = "1234567890"

    # Create breedbase connection schema
    breedbase_connection_in = schemas.BreedbaseConnectionCreate(
        base_url=base_url,
        trial_id=trial_id,
    )

    # Create breedbase connection in database
    breedbase_connection = crud.breedbase_connection.create_with_project(
        db, obj_in=breedbase_connection_in, project_id=project.id
    )

    # Verify that the breedbase connection was created
    assert breedbase_connection is not None
    assert breedbase_connection.project_id == project.id
    assert breedbase_connection.trial_id == trial_id


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
    assert breedbase_connection_from_db.trial_id == breedbase_connection.trial_id
    assert breedbase_connection_from_db.base_url == breedbase_connection.base_url


def test_get_breedbase_connection_by_trial_id(db: Session) -> None:
    # Create project
    project = create_project(db)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # Get breedbase connection from database
    breedbase_connection_from_db = crud.breedbase_connection.get_by_trial_id(
        db, trial_id=breedbase_connection.trial_id
    )

    # Verify that the breedbase connection was created
    assert breedbase_connection_from_db is not None
    assert breedbase_connection_from_db.project_id == project.id
    assert breedbase_connection_from_db.trial_id == breedbase_connection.trial_id
    assert breedbase_connection_from_db.base_url == breedbase_connection.base_url


def test_update_breedbase_connection(db: Session) -> None:
    # Create project
    project = create_project(db)

    # Create breedbase connection
    breedbase_connection = create_breedbase_connection(db, project.id)

    # New trial ID
    new_trial_id = "1111111111"

    # Update breedbase connection
    breedbase_connection_in = schemas.BreedbaseConnectionUpdate(
        base_url="https://example.com",
        trial_id=new_trial_id,
    )

    # Update breedbase connection in database
    breedbase_connection_updated = crud.breedbase_connection.update(
        db, db_obj=breedbase_connection, obj_in=breedbase_connection_in
    )

    # Verify that the breedbase connection was updated
    assert breedbase_connection_updated is not None
    assert breedbase_connection_updated.project_id == project.id
    assert breedbase_connection_updated.trial_id == new_trial_id


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
    assert removed_breedbase_connection.trial_id == breedbase_connection.trial_id

    # Get breedbase connection from database
    breedbase_connection_from_db = crud.breedbase_connection.get(
        db, id=breedbase_connection.id
    )

    # Verify that the breedbase connection was removed
    assert breedbase_connection_from_db is None
