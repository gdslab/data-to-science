import os

import geopandas as gpd
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
from app.tests.utils.utils import get_geojson_feature_collection
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
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
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
        db, role=Role.VIEWER, member_id=current_user.id, project_id=project.id
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
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
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
        db, role=Role.VIEWER, member_id=current_user.id, project_id=project.id
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
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
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
        db, role=Role.VIEWER, member_id=current_user.id, project_id=project.id
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


def test_update_vector_layer_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    feature_collection = create_feature_collection(db, "point", project_id=project.id)
    layer_id = feature_collection.features[0].properties["layer_id"]
    new_layer_name = "Updated Point Layer"

    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{layer_id}",
        json={"layer_name": new_layer_name},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    response_fc = VectorLayerFeatureCollection(**response_data)
    assert len(response_fc.features) == 1
    assert response_fc.features[0].properties["layer_name"] == new_layer_name


def test_update_vector_layer_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
    )
    feature_collection = create_feature_collection(db, "point", project_id=project.id)
    layer_id = feature_collection.features[0].properties["layer_id"]
    new_layer_name = "Updated Point Layer"

    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{layer_id}",
        json={"layer_name": new_layer_name},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    response_fc = VectorLayerFeatureCollection(**response_data)
    assert response_fc.features[0].properties["layer_name"] == new_layer_name


def test_update_vector_layer_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_id=project.id
    )
    feature_collection = create_feature_collection(db, "point", project_id=project.id)
    layer_id = feature_collection.features[0].properties["layer_id"]

    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{layer_id}",
        json={"layer_name": "Should Not Update"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_vector_layer_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    feature_collection = create_feature_collection(db, "point", project_id=project.id)
    layer_id = feature_collection.features[0].properties["layer_id"]

    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{layer_id}",
        json={"layer_name": "Should Not Update"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_vector_layer_with_multiple_features(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    # Create multipoint feature collection with 3 features
    feature_collection = create_feature_collection(
        db, "multipoint", project_id=project.id
    )
    layer_id = feature_collection.features[0].properties["layer_id"]
    new_layer_name = "Updated Multipoint Layer"

    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{layer_id}",
        json={"layer_name": new_layer_name},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    response_fc = VectorLayerFeatureCollection(**response_data)
    # All 3 features should have the updated name
    assert len(response_fc.features) == 3
    for feature in response_fc.features:
        assert feature.properties["layer_name"] == new_layer_name


def test_update_vector_layer_not_found(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    non_existent_layer_id = "nonexistent"

    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/{non_existent_layer_id}",
        json={"layer_name": "Should Not Work"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_vector_layer_from_geojson_with_point(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    vector_layer_data = get_geojson_feature_collection("point")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=vector_layer_data,
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["type"] == "FeatureCollection"
    assert len(response_data["features"]) == 1
    assert response_data["features"][0]["geometry"]["type"] == "Point"
    assert response_data["features"][0]["properties"]["layer_name"] == "Point Example"
    assert "layer_id" in response_data["features"][0]["properties"]
    assert "preview_url" in response_data["metadata"]


def test_create_vector_layer_from_geojson_with_linestring(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    vector_layer_data = get_geojson_feature_collection("linestring")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=vector_layer_data,
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["type"] == "FeatureCollection"
    assert len(response_data["features"]) == 1
    assert response_data["features"][0]["geometry"]["type"] == "LineString"
    assert (
        response_data["features"][0]["properties"]["layer_name"] == "Linestring Example"
    )


def test_create_vector_layer_from_geojson_with_polygon(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    vector_layer_data = get_geojson_feature_collection("polygon")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=vector_layer_data,
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["type"] == "FeatureCollection"
    assert len(response_data["features"]) == 1
    assert response_data["features"][0]["geometry"]["type"] == "Polygon"
    assert response_data["features"][0]["properties"]["layer_name"] == "Polygon Example"


def test_create_vector_layer_from_geojson_with_multiple_features(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    vector_layer_data = get_geojson_feature_collection("multipoint")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=vector_layer_data,
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["type"] == "FeatureCollection"
    assert len(response_data["features"]) == 3
    # All features should have the same layer_id
    layer_id = response_data["features"][0]["properties"]["layer_id"]
    for feature in response_data["features"]:
        assert feature["properties"]["layer_id"] == layer_id


def test_create_vector_layer_from_geojson_with_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_id=project.id
    )
    vector_layer_data = get_geojson_feature_collection("point")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=vector_layer_data,
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_create_vector_layer_from_geojson_with_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_id=project.id
    )
    vector_layer_data = get_geojson_feature_collection("point")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=vector_layer_data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_vector_layer_from_geojson_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    project = create_project(db)
    vector_layer_data = get_geojson_feature_collection("point")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=vector_layer_data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_vector_layer_from_geojson_with_invalid_longitude(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    vector_layer_data = get_geojson_feature_collection("invalid_longitude")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=vector_layer_data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "longitude" in response.json()["detail"].lower()


def test_create_vector_layer_from_geojson_with_invalid_latitude(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    vector_layer_data = get_geojson_feature_collection("invalid_latitude")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=vector_layer_data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "latitude" in response.json()["detail"].lower()


def test_create_vector_layer_from_geojson_with_empty_features(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    vector_layer_data = get_geojson_feature_collection("empty_features")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=vector_layer_data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "at least one feature" in response.json()["detail"].lower()


def test_create_vector_layer_from_geojson_generates_parquet(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that creating a vector layer from GeoJSON also generates a parquet file."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)

    # Test with Point geometry
    point_data = get_geojson_feature_collection("point")
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=point_data,
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    point_layer_id = response_data["features"][0]["properties"]["layer_id"]

    # Verify parquet file was created
    parquet_path = os.path.join(
        settings.TEST_STATIC_DIR,
        "projects",
        str(project.id),
        "vector",
        point_layer_id,
        f"{point_layer_id}.parquet",
    )
    assert os.path.exists(parquet_path)

    # Verify parquet file can be read and contains correct data
    gdf = gpd.read_parquet(parquet_path)
    assert len(gdf) == 1
    assert gdf.iloc[0].geometry.geom_type == "Point"

    # Test with Polygon geometry
    polygon_data = get_geojson_feature_collection("polygon")
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=polygon_data,
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    polygon_layer_id = response_data["features"][0]["properties"]["layer_id"]

    # Verify parquet file for polygon
    parquet_path_polygon = os.path.join(
        settings.TEST_STATIC_DIR,
        "projects",
        str(project.id),
        "vector",
        polygon_layer_id,
        f"{polygon_layer_id}.parquet",
    )
    assert os.path.exists(parquet_path_polygon)
    gdf_polygon = gpd.read_parquet(parquet_path_polygon)
    assert len(gdf_polygon) == 1
    assert gdf_polygon.iloc[0].geometry.geom_type == "Polygon"


def test_create_vector_layer_from_geojson_generates_flatgeobuf(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that creating a vector layer from GeoJSON also generates a FlatGeobuf file."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)

    # Test with Point geometry
    point_data = get_geojson_feature_collection("point")
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=point_data,
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    point_layer_id = response_data["features"][0]["properties"]["layer_id"]

    # Verify FlatGeobuf file was created
    fgb_path = os.path.join(
        settings.TEST_STATIC_DIR,
        "projects",
        str(project.id),
        "vector",
        point_layer_id,
        f"{point_layer_id}.fgb",
    )
    assert os.path.exists(fgb_path)

    # Verify FlatGeobuf file can be read and contains correct data
    gdf = gpd.read_file(fgb_path)
    assert len(gdf) == 1
    assert gdf.iloc[0].geometry.geom_type == "Point"

    # Test with Polygon geometry
    polygon_data = get_geojson_feature_collection("polygon")
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/vector_layers/geojson",
        json=polygon_data,
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    polygon_layer_id = response_data["features"][0]["properties"]["layer_id"]

    # Verify FlatGeobuf file for polygon
    fgb_path_polygon = os.path.join(
        settings.TEST_STATIC_DIR,
        "projects",
        str(project.id),
        "vector",
        polygon_layer_id,
        f"{polygon_layer_id}.fgb",
    )
    assert os.path.exists(fgb_path_polygon)
    gdf_polygon = gpd.read_file(fgb_path_polygon)
    assert len(gdf_polygon) == 1
    assert gdf_polygon.iloc[0].geometry.geom_type == "Polygon"
