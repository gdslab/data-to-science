import pytest
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from app import crud
from app.schemas.dataset import DatasetUpdate
from app.tests.utils.dataset import create_random_dataset
from app.tests.utils.project import create_random_project


def test_create_dataset(db: Session) -> None:
    """Verify new dataset is created in database."""
    project = create_random_project(db)
    dataset = create_random_dataset(db, category="UAS", project_id=project.id)
    assert dataset
    assert "UAS" == dataset.category
    assert project.id == dataset.project_id


def test_create_dataset_with_invalid_category(db: Session) -> None:
    """Verify exception raised for invalid dataset category."""
    project = create_random_project(db)
    with pytest.raises(DataError):
        create_random_dataset(db, category="Invalid", project_id=project.id)


def test_get_dataset(db: Session) -> None:
    """Verify retrieving dataset by id returns correct dataset."""
    project = create_random_project(db)
    dataset = create_random_dataset(db, category="UAS", project_id=project.id)
    stored_dataset = crud.dataset.get(db, id=dataset.id)
    assert stored_dataset
    assert dataset.id == stored_dataset.id
    assert dataset.category == stored_dataset.category
    assert dataset.project_id == stored_dataset.project_id


def test_get_datasets(db: Session) -> None:
    """Verify retrieval of multiple datasets belonging to same project."""
    project = create_random_project(db)
    create_random_dataset(db, category="UAS", project_id=project.id)
    create_random_dataset(db, category="UAS", project_id=project.id)
    project_datasets = crud.dataset.get_project_dataset_list(db, project_id=project.id)
    assert type(project_datasets) is list
    assert len(project_datasets) > 1
    for dataset in project_datasets:
        assert "category" in dataset.__dict__
        assert "project_id" in dataset.__dict__
        assert project.id == dataset.project_id


def test_update_dataset(db: Session) -> None:
    """Verify update changes dataset attributes in database."""
    project = create_random_project(db)
    dataset = create_random_dataset(db, category="UAS", project_id=project.id)
    dataset_in_update = DatasetUpdate(
        category="Ground",
    )
    dataset_update = crud.dataset.update(db, db_obj=dataset, obj_in=dataset_in_update)
    assert dataset.id == dataset_update.id
    assert dataset.project_id == dataset_update.project_id
    assert dataset_in_update.category == dataset_update.category


def test_update_dataset_to_invalid_category(db: Session) -> None:
    """Verify update rejects invalid category."""
    project = create_random_project(db)
    dataset = create_random_dataset(db, category="UAS", project_id=project.id)
    dataset_in_update = DatasetUpdate(
        category="Invalid",
    )
    with pytest.raises(DataError):
        crud.dataset.update(db, db_obj=dataset, obj_in=dataset_in_update)
