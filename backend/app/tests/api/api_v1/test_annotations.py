from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.enums.visibility import Visibility
from app.schemas.role import Role
from app.tests.utils.annotation import (
    create_annotation,
    create_annotation_in,
    create_multiple_annotations,
)
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def test_create_annotation_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating an annotation with project owner role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation_in = create_annotation_in(description="Owner's annotation")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_in.model_dump(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert "id" in response_data
    assert response_data["description"] == "Owner's annotation"
    assert "geom" in response_data
    assert response_data["data_product_id"] == str(data_product.obj.id)
    assert response_data["created_by_id"] == str(current_user.id)


def test_create_annotation_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating an annotation with project manager role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
    )
    annotation_in = create_annotation_in(description="Manager's annotation")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_in.model_dump(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["description"] == "Manager's annotation"
    assert response_data["created_by_id"] == str(current_user.id)


def test_create_personal_annotation_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that a viewer can create a personal (OWNER) annotation."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.VIEWER,
    )
    annotation_in = create_annotation_in(description="Viewer's annotation")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_in.model_dump(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["description"] == "Viewer's annotation"
    assert response_data["visibility"] == "OWNER"
    assert response_data["created_by_id"] == str(current_user.id)


def test_create_project_annotation_with_viewer_role_forbidden(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that a viewer cannot create a PROJECT-level annotation."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.VIEWER,
    )
    annotation_in = create_annotation_in(description="Viewer's project annotation")
    annotation_data = annotation_in.model_dump()
    annotation_data["visibility"] = "PROJECT"

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_data,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_annotation_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating an annotation without project access."""
    data_product = SampleDataProduct(db)
    annotation_in = create_annotation_in(description="Unauthorized annotation")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_in.model_dump(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_annotation_with_different_geometry_types(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating annotations with different geometry types."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    geometry_types = ["Point", "LineString", "Polygon"]

    for geom_type in geometry_types:
        annotation_in = create_annotation_in(
            description=f"{geom_type} annotation", geometry_type=geom_type
        )

        response = client.post(
            f"{settings.API_V1_STR}/projects/{data_product.project.id}"
            f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
            json=annotation_in.model_dump(),
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["description"] == f"{geom_type} annotation"
        assert response_data["geom"]["geometry"]["type"] == geom_type


def test_get_annotation_by_id_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting an annotation by ID with project owner role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation = create_annotation(
        db, data_product_id=data_product.obj.id, created_by_id=current_user.id
    )

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(annotation.id)
    assert response_data["description"] == annotation.description
    assert "created_by" in response_data
    assert response_data["created_by"]["id"] == str(current_user.id)


def test_get_annotation_by_id_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting an annotation by ID with project viewer role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.VIEWER,
    )
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(annotation.id)


def test_get_annotation_by_id_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting an annotation by ID without project access."""
    data_product = SampleDataProduct(db)
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_annotation_by_id_not_found(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting a non-existent annotation by ID."""
    from uuid import uuid4

    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    fake_annotation_id = uuid4()

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{fake_annotation_id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_annotation_from_different_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting an annotation that belongs to a different data product."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product_1 = SampleDataProduct(db, user=current_user)
    data_product_2 = SampleDataProduct(db, user=current_user)

    # Create annotation for data_product_1
    annotation = create_annotation(db, data_product_id=data_product_1.obj.id)

    # Try to get annotation via data_product_2's URL
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product_2.project.id}"
        f"/flights/{data_product_2.flight.id}/data_products/{data_product_2.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_annotations_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting all annotations for a data product with project owner role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotations = create_multiple_annotations(
        db, count=3, data_product_id=data_product.obj.id, created_by_id=current_user.id
    )

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 3

    annotation_ids = {str(a.id) for a in annotations}
    for annotation_data in response_data:
        assert annotation_data["id"] in annotation_ids
        assert "description" in annotation_data
        assert "geom" in annotation_data


def test_get_annotations_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting all annotations for a data product with project viewer role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.VIEWER,
    )
    # Create PROJECT-visible annotations so the viewer can see them
    create_multiple_annotations(
        db,
        count=2,
        data_product_id=data_product.obj.id,
        visibility=Visibility.PROJECT,
    )

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 2


def test_get_annotations_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting annotations without project access."""
    data_product = SampleDataProduct(db)
    create_multiple_annotations(db, count=2, data_product_id=data_product.obj.id)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_annotations_returns_empty_list(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting annotations when none exist."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 0


def test_update_annotation_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation with project owner role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation = create_annotation(
        db,
        description="Original description",
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
    )

    update_data = {"description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(annotation.id)
    assert response_data["description"] == "Updated description"


def test_update_annotation_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation with project manager role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
    )
    annotation = create_annotation(
        db, description="Original", data_product_id=data_product.obj.id
    )

    update_data = {"description": "Manager updated"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["description"] == "Manager updated"


def test_update_annotation_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation with project viewer role (should fail)."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.VIEWER,
    )
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    update_data = {"description": "Viewer update attempt"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_annotation_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation without project access."""
    data_product = SampleDataProduct(db)
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    update_data = {"description": "Unauthorized update"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_annotation_geometry(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation's geometry."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation = create_annotation(
        db,
        geometry_type="Point",
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
    )

    # Create new geometry
    new_annotation_in = create_annotation_in(geometry_type="Polygon")
    update_data = {"geom": new_annotation_in.geom.model_dump()}

    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(annotation.id)
    assert response_data["geom"]["geometry"]["type"] == "Polygon"


def test_update_annotation_not_found(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating a non-existent annotation."""
    from uuid import uuid4

    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    fake_annotation_id = uuid4()

    update_data = {"description": "Update non-existent"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{fake_annotation_id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_annotation_from_different_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation that belongs to a different data product."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product_1 = SampleDataProduct(db, user=current_user)
    data_product_2 = SampleDataProduct(db, user=current_user)

    # Create annotation for data_product_1
    annotation = create_annotation(db, data_product_id=data_product_1.obj.id)

    # Try to update annotation via data_product_2's URL
    update_data = {"description": "Wrong data product update"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product_2.project.id}"
        f"/flights/{data_product_2.flight.id}/data_products/{data_product_2.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_annotation_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting an annotation with project owner role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation = create_annotation(
        db, data_product_id=data_product.obj.id, created_by_id=current_user.id
    )

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(annotation.id)

    # Verify annotation is deleted
    deleted_annotation = crud.annotation.get(db, id=annotation.id)
    assert deleted_annotation is None


def test_delete_annotation_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting an annotation with project manager role (should fail)."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
    )
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_annotation_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting an annotation with project viewer role (should fail)."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.VIEWER,
    )
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_annotation_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting an annotation without project access."""
    data_product = SampleDataProduct(db)
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_annotation_not_found(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting a non-existent annotation."""
    from uuid import uuid4

    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    fake_annotation_id = uuid4()

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{fake_annotation_id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_annotation_from_different_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting an annotation that belongs to a different data product."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product_1 = SampleDataProduct(db, user=current_user)
    data_product_2 = SampleDataProduct(db, user=current_user)

    # Create annotation for data_product_1
    annotation = create_annotation(db, data_product_id=data_product_1.obj.id)

    # Try to delete annotation via data_product_2's URL
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product_2.project.id}"
        f"/flights/{data_product_2.flight.id}/data_products/{data_product_2.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_annotation_with_tags(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating an annotation with tags via API."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation_in = create_annotation_in(description="Annotation with tags")

    # Add tags to the request
    annotation_data = annotation_in.model_dump()
    annotation_data["tags"] = ["species", "flowering", "drought-resistant"]

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_data,
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert "id" in response_data
    assert response_data["description"] == "Annotation with tags"
    assert "tag_rows" in response_data
    assert len(response_data["tag_rows"]) == 3

    tag_names = {tag_row["tag"]["name"] for tag_row in response_data["tag_rows"]}
    assert tag_names == {"species", "flowering", "drought-resistant"}


def test_create_annotation_with_empty_tags(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating an annotation with empty tags list via API."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation_in = create_annotation_in(description="Annotation without tags")

    annotation_data = annotation_in.model_dump()
    annotation_data["tags"] = []

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_data,
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert "tag_rows" in response_data
    assert len(response_data["tag_rows"]) == 0


def test_update_annotation_add_tags_via_api(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test adding tags to an existing annotation via API."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation = create_annotation(
        db,
        description="Annotation to add tags to",
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
    )

    update_data = {"tags": ["new-tag-1", "new-tag-2"]}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "tag_rows" in response_data
    assert len(response_data["tag_rows"]) == 2

    tag_names = {tag_row["tag"]["name"] for tag_row in response_data["tag_rows"]}
    assert tag_names == {"new-tag-1", "new-tag-2"}


def test_update_annotation_remove_tags_via_api(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test removing tags from an annotation via API."""
    from app.schemas.annotation import AnnotationCreate

    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    # Create annotation with tags using CRUD
    annotation_in = create_annotation_in(description="Annotation with tags to remove")
    annotation_create = AnnotationCreate(
        description=annotation_in.description,
        geom=annotation_in.geom,
        tags=["tag-1", "tag-2", "tag-3"],
    )
    annotation = crud.annotation.create_with_data_product(
        db=db,
        obj_in=annotation_create,
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
    )

    # Update to remove all tags via API
    update_data: dict = {"tags": []}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "tag_rows" in response_data
    assert len(response_data["tag_rows"]) == 0


def test_update_annotation_modify_tags_via_api(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test modifying tags on an annotation via API."""
    from app.schemas.annotation import AnnotationCreate

    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    # Create annotation with initial tags
    annotation_in = create_annotation_in(description="Annotation with tags to modify")
    annotation_create = AnnotationCreate(
        description=annotation_in.description,
        geom=annotation_in.geom,
        tags=["keep", "remove-1", "remove-2"],
    )
    annotation = crud.annotation.create_with_data_product(
        db=db,
        obj_in=annotation_create,
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
    )

    # Update tags: keep "keep", remove "remove-1" and "remove-2", add "new-1" and "new-2"
    update_data = {"tags": ["keep", "new-1", "new-2"]}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "tag_rows" in response_data
    assert len(response_data["tag_rows"]) == 3

    tag_names = {tag_row["tag"]["name"] for tag_row in response_data["tag_rows"]}
    assert tag_names == {"keep", "new-1", "new-2"}


def test_get_annotation_returns_tags(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that getting an annotation returns its tags."""
    from app.schemas.annotation import AnnotationCreate

    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    # Create annotation with tags
    annotation_in = create_annotation_in(description="Annotation with tags")
    annotation_create = AnnotationCreate(
        description=annotation_in.description,
        geom=annotation_in.geom,
        tags=["tag-a", "tag-b"],
    )
    annotation = crud.annotation.create_with_data_product(
        db=db,
        obj_in=annotation_create,
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
    )

    # Get the annotation via API
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "tag_rows" in response_data
    assert len(response_data["tag_rows"]) == 2

    tag_names = {tag_row["tag"]["name"] for tag_row in response_data["tag_rows"]}
    assert tag_names == {"tag-a", "tag-b"}


def test_get_annotations_hides_other_users_personal_annotations(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that User A cannot see User B's personal (OWNER) annotations."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    # Create a second user and add them to the project
    other_user = create_user(db)
    create_project_member(
        db,
        member_id=other_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
    )

    # Other user creates a personal (OWNER) annotation
    create_annotation(
        db,
        description="Other user's personal annotation",
        data_product_id=data_product.obj.id,
        created_by_id=other_user.id,
        visibility=Visibility.OWNER,
    )

    # Current user creates their own personal annotation
    create_annotation(
        db,
        description="My personal annotation",
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
        visibility=Visibility.OWNER,
    )

    # Current user should only see their own annotation
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["description"] == "My personal annotation"


def test_get_annotations_shows_other_users_project_annotations(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that User A can see User B's project-level annotations."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    # Create a second user and add them to the project
    other_user = create_user(db)
    create_project_member(
        db,
        member_id=other_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
    )

    # Other user creates a project-level annotation
    create_annotation(
        db,
        description="Other user's project annotation",
        data_product_id=data_product.obj.id,
        created_by_id=other_user.id,
        visibility=Visibility.PROJECT,
    )

    # Current user creates their own personal annotation
    create_annotation(
        db,
        description="My personal annotation",
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
        visibility=Visibility.OWNER,
    )

    # Current user should see both annotations
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 2
    descriptions = {a["description"] for a in response_data}
    assert descriptions == {
        "Other user's project annotation",
        "My personal annotation",
    }


def test_create_annotation_with_style(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating an annotation with a style."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation_in = create_annotation_in(description="Styled annotation")

    annotation_data = annotation_in.model_dump()
    annotation_data["style"] = {"color": "#ff0000", "fill": "#ff9999", "opacity": 80}

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_data,
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["style"] == {
        "color": "#ff0000",
        "fill": "#ff9999",
        "opacity": 80,
    }


def test_create_annotation_without_style_returns_null(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating an annotation without a style returns null."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation_in = create_annotation_in(description="No style annotation")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_in.model_dump(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["style"] is None


def test_update_annotation_style(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation's style."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation = create_annotation(
        db,
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
    )

    update_data = {"style": {"color": "#00ff00", "fill": "#99ff99", "opacity": 50}}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["style"] == {
        "color": "#00ff00",
        "fill": "#99ff99",
        "opacity": 50,
    }


def test_get_annotations_returns_persisted_styles(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that GET annotations returns persisted styles."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation_in = create_annotation_in(description="Styled annotation")

    annotation_data = annotation_in.model_dump()
    annotation_data["style"] = {"color": "#0000ff", "fill": "#9999ff", "opacity": 60}

    # Create annotation with style
    client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_data,
    )

    # Fetch annotations and verify style persists
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["style"] == {
        "color": "#0000ff",
        "fill": "#9999ff",
        "opacity": 60,
    }


def test_delete_own_owner_annotation_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that a manager can delete their own personal (OWNER) annotation."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
    )
    annotation = create_annotation(
        db,
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
        visibility=Visibility.OWNER,
    )

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert crud.annotation.get(db, id=annotation.id) is None


def test_delete_own_project_annotation_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that a manager can delete their own shared (PROJECT) annotation."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
    )
    annotation = create_annotation(
        db,
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
        visibility=Visibility.PROJECT,
    )

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert crud.annotation.get(db, id=annotation.id) is None


def test_project_owner_can_delete_other_users_project_annotation(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that a project owner can delete another user's shared (PROJECT) annotation."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    other_user = create_user(db)
    create_project_member(
        db,
        member_id=other_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
    )

    annotation = create_annotation(
        db,
        data_product_id=data_product.obj.id,
        created_by_id=other_user.id,
        visibility=Visibility.PROJECT,
    )

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert crud.annotation.get(db, id=annotation.id) is None


def test_manager_cannot_delete_other_users_project_annotation(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that a manager cannot delete another user's shared (PROJECT) annotation."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
    )

    other_user = create_user(db)
    annotation = create_annotation(
        db,
        data_product_id=data_product.obj.id,
        created_by_id=other_user.id,
        visibility=Visibility.PROJECT,
    )

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_project_owner_cannot_delete_other_users_personal_annotation(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that a project owner cannot delete another user's personal (OWNER) annotation."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    other_user = create_user(db)
    create_project_member(
        db,
        member_id=other_user.id,
        project_uuid=data_product.project.id,
        role=Role.MANAGER,
    )

    annotation = create_annotation(
        db,
        data_product_id=data_product.obj.id,
        created_by_id=other_user.id,
        visibility=Visibility.OWNER,
    )

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
