import os

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.role import Role
from app.schemas.vector_layer import VectorLayerFeatureCollection
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.vector_layers import create_feature_collection


def test_read_vector_layer_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    point_feature_collection = create_feature_collection(db, "point", project.id)
    vector_layer_feature_id = point_feature_collection.features[0].properties[
        "feature_id"
    ]

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{vector_layer_feature_id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    response_feature = VectorLayerFeatureCollection(**response_data)
    assert response_feature.features[0].properties["feature_id"]
    assert response_feature.features[0].properties["project_id"] == str(project.id)
    assert (
        response_feature.features[0].properties["feature_id"]
        == point_feature_collection.features[0].properties["feature_id"]
    )
    assert response_feature.metadata.preview_url
    assert os.path.exists(
        f"{settings.TEST_STATIC_DIR}/projects/{project.id}/vector/{response_feature.features[0].properties['layer_id']}/preview.png"
    )


def test_read_vector_layer_with_manager_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    point_feature_collection = create_feature_collection(db, "point", project.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
    )
    vector_layer_feature_id = point_feature_collection.features[0].properties[
        "feature_id"
    ]

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{vector_layer_feature_id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    response_feature = VectorLayerFeatureCollection(**response_data)
    assert response_feature.features[0].properties["feature_id"]
    assert response_feature.features[0].properties["project_id"] == str(project.id)
    assert (
        response_feature.features[0].properties["feature_id"]
        == point_feature_collection.features[0].properties["feature_id"]
    )
    assert response_feature.metadata.preview_url
    assert os.path.exists(
        f"{settings.TEST_STATIC_DIR}/projects/{project.id}/vector/{response_feature.features[0].properties['layer_id']}/preview.png"
    )


def test_read_vector_layer_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    point_feature_collection = create_feature_collection(db, "point", project.id)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )
    vector_layer_feature_id = point_feature_collection.features[0].properties[
        "feature_id"
    ]

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{vector_layer_feature_id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    response_feature = VectorLayerFeatureCollection(**response_data)
    assert response_feature.features[0].properties["feature_id"]
    assert response_feature.features[0].properties["project_id"] == str(project.id)
    assert (
        response_feature.features[0].properties["feature_id"]
        == point_feature_collection.features[0].properties["feature_id"]
    )
    assert response_feature.metadata.preview_url
    assert os.path.exists(
        f"{settings.TEST_STATIC_DIR}/projects/{project.id}/vector/{response_feature.features[0].properties['layer_id']}/preview.png"
    )


def test_read_vector_layer_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    point_feature_collection = create_feature_collection(db, "point", project.id)
    vector_layer_feature_id = point_feature_collection.features[0].properties[
        "feature_id"
    ]

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{vector_layer_feature_id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_vector_layer_with_multiple_features(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    # creates feature collection with three features
    multipoint_feature_collection = create_feature_collection(
        db, "multipoint", project.id
    )
    vector_layer_feature_id = multipoint_feature_collection.features[0].properties[
        "feature_id"
    ]

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{vector_layer_feature_id}"
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    response_feature_collection = VectorLayerFeatureCollection(**response_data)
    assert len(response_feature_collection.features) == 3
    # check that each feature has the same layer_id
    layer_id = response_feature_collection.features[0].properties["layer_id"]
    for feature in response_feature_collection.features:
        assert feature.properties["layer_id"] == layer_id


def test_read_vector_layers_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    fc1 = create_feature_collection(db, "point", project.id)
    fc2 = create_feature_collection(db, "linestring", project_id=project.id)
    fc3 = create_feature_collection(db, "polygon", project_id=project.id)

    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/vector_layers")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 3
    for layer in response_data:
        assert "layer_id" in layer
        assert "layer_name" in layer
        assert "geom_type" in layer
        assert "signed_url" in layer
        assert "preview_url" in layer
        assert os.path.exists(layer["preview_url"].split(settings.API_DOMAIN)[1])


def test_read_vector_layers_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    fc1 = create_feature_collection(db, "point", project.id)
    fc2 = create_feature_collection(db, "linestring", project_id=project.id)
    fc3 = create_feature_collection(db, "polygon", project_id=project.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
    )

    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/vector_layers")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 3
    for layer in response_data:
        assert "layer_id" in layer
        assert "layer_name" in layer
        assert "geom_type" in layer
        assert "signed_url" in layer
        assert "preview_url" in layer
        assert os.path.exists(layer["preview_url"].split(settings.API_DOMAIN)[1])


def test_read_vector_layers_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    fc1 = create_feature_collection(db, "point", project.id)
    fc2 = create_feature_collection(db, "linestring", project_id=project.id)
    fc3 = create_feature_collection(db, "polygon", project_id=project.id)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )

    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/vector_layers")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 3
    for layer in response_data:
        assert "layer_id" in layer
        assert "layer_name" in layer
        assert "geom_type" in layer
        assert "signed_url" in layer
        assert "preview_url" in layer
        assert os.path.exists(layer["preview_url"].split(settings.API_DOMAIN)[1])


def test_read_vector_layers_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    create_feature_collection(db, "point", project.id)
    create_feature_collection(db, "linestring", project_id=project.id)
    create_feature_collection(db, "polygon", project_id=project.id)

    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/vector_layers")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_read_vector_layers_in_geojson_format_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    fc1 = create_feature_collection(db, "point", project.id)
    fc2 = create_feature_collection(db, "linestring", project_id=project.id)
    fc3 = create_feature_collection(db, "polygon", project_id=project.id)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers",
        params={"format": "json"},
    )
    assert response.status_code == status.HTTP_200_OK
    response_feature_collections = response.json()
    assert isinstance(response_feature_collections, list)
    assert len(response_feature_collections) == 3
    for feature_collection in response_feature_collections:
        feature_collection = VectorLayerFeatureCollection(**feature_collection)
        for feature in feature_collection.features:
            assert feature.properties["feature_id"] in [
                fc1.features[0].properties["feature_id"],
                fc2.features[0].properties["feature_id"],
                fc3.features[0].properties["feature_id"],
            ]
        assert feature_collection.metadata.preview_url
        assert os.path.exists(
            f"{settings.TEST_STATIC_DIR}/projects/{project.id}/vector/{feature_collection.features[0].properties['layer_id']}/preview.png"
        )


def test_remove_vector_layer_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    feature_collection = create_feature_collection(
        db, geom_type="multipoint", project_id=project.id
    )
    layer_id = feature_collection.features[0].properties["layer_id"]

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{layer_id}"
    )
    assert response.status_code == status.HTTP_200_OK

    removed_vector_layer = crud.vector_layer.get_vector_layer_by_id(
        db, project_id=project.id, layer_id=layer_id
    )
    assert len(removed_vector_layer) == 0


def test_remove_vector_layer_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
    )
    feature_collection = create_feature_collection(
        db, geom_type="multipoint", project_id=project.id
    )
    layer_id = feature_collection.features[0].properties["layer_id"]

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{layer_id}"
    )
    assert response.status_code == status.HTTP_200_OK

    removed_vector_layer = crud.vector_layer.get_vector_layer_by_id(
        db, project_id=project.id, layer_id=layer_id
    )
    assert len(removed_vector_layer) == 0


def test_remove_vector_layer_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )
    feature_collection = create_feature_collection(
        db, geom_type="multipoint", project_id=project.id
    )
    layer_id = feature_collection.features[0].properties["layer_id"]

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{layer_id}"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_remove_vector_layer_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    feature_collection = create_feature_collection(
        db, geom_type="multipoint", project_id=project.id
    )
    layer_id = feature_collection.features[0].properties["layer_id"]

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{layer_id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
