from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_approved_user
from app.core.config import settings
from app.schemas.dataset import DatasetUpdate
from app.tests.utils.dataset import create_random_dataset
from app.tests.utils.project import create_random_project


def test_create_dataset(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify new dataset is created in database."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_token_headers["Authorization"].split(" ")[1]),
    )
    project = create_random_project(db, owner_id=current_user.id)
    data = {"category": "UAS"}
    r = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/datasets",
        headers=normal_user_token_headers,
        json=data,
    )
    assert 201 == r.status_code
    content = r.json()
    assert "id" in content
    assert str(project.id) == content["project_id"]
    assert data["category"] == content["category"]


def test_get_datasets(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify retrieval of datasets in project."""
    # create two datasets for a project the current user can view
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_token_headers["Authorization"].split(" ")[1]),
    )
    project = create_random_project(db, owner_id=current_user.id)
    dataset1 = create_random_dataset(db, category="UAS", project_id=project.id)
    dataset2 = create_random_dataset(db, category="Ground", project_id=project.id)
    # create third dataset the current user does not have permission to view
    create_random_dataset(db, category="UAS", project_id=create_random_project(db).id)
    # request list of datasets associated with project current user can view
    r = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/datasets/",
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    datasets = r.json()
    assert type(datasets) is list
    assert len(datasets) == 2
    for dataset in datasets:
        assert "category" in dataset
        assert "project_id" in dataset
        assert str(project.id) == dataset["project_id"]
        assert str(dataset1.id) == dataset["id"] or str(dataset2.id) == dataset["id"]


def test_get_dataset_for_project_current_user_can_view(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify retrieval of dataset for project current user can view."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_token_headers["Authorization"].split(" ")[1]),
    )
    project = create_random_project(db, owner_id=current_user.id)
    dataset = create_random_dataset(db, category="UAS", project_id=project.id)
    r = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/datasets/{dataset.id}",
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    response_data = r.json()
    assert str(dataset.id) == response_data["id"]
    assert str(dataset.project_id) == response_data["project_id"]
    assert dataset.category == response_data["category"]


def test_get_dataset_for_project_current_user_cannot_view(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify failure to retrieve dataset from project current user cannot view."""
    dataset = create_random_dataset(db, category="UAS")
    r = client.get(
        f"{settings.API_V1_STR}/projects/{dataset.project_id}/datasets/{dataset.id}",
        headers=normal_user_token_headers,
    )
    assert 404 == r.status_code


def test_update_dataset_for_project_current_user_can_access(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify update of dataset from project current user can access."""
    current_user = get_current_approved_user(
        get_current_user(db, normal_user_token_headers["Authorization"].split(" ")[1]),
    )
    project = create_random_project(db, owner_id=current_user.id)
    dataset = create_random_dataset(db, category="UAS", project_id=project.id)
    dataset_in = DatasetUpdate(category="Ground")
    r = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/datasets/{dataset.id}",
        json=dataset_in.dict(),
        headers=normal_user_token_headers,
    )
    assert 200 == r.status_code
    updated_dataset = r.json()
    assert str(dataset.id) == updated_dataset["id"]
    assert str(project.id) == updated_dataset["project_id"]
    assert dataset_in.category == updated_dataset["category"]


def test_update_dataset_for_project_current_user_cannot_access(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """Verify failure to update dataset from project current user cannot access."""
    dataset = create_random_dataset(db, category="UAS")
    dataset_in = DatasetUpdate(category="Ground")
    r = client.put(
        f"{settings.API_V1_STR}/projects/{dataset.project_id}/datasets/{dataset.id}",
        json=dataset_in.dict(),
        headers=normal_user_token_headers,
    )
    assert 404 == r.status_code
