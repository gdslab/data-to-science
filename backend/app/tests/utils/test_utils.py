import os
from uuid import UUID

import geopandas as gpd
from sqlalchemy.orm import Session

from app import crud
from app.api.utils import (
    create_vector_layer_preview,
    save_vector_layer_parquet,
    save_vector_layer_flatgeobuf,
    get_static_dir,
)
from app.core.config import settings
from app.utils.ProtectedStaticFiles import (
    parse_vector_parquet_path,
    parse_vector_flatgeobuf_path,
)
from app.tests.utils.project import create_project
from app.tests.utils.utils import VectorLayerDict
from app.tests.utils.vector_layers import (
    get_geojson_feature_collection,
)


def test_create_vector_layer_preview_image(
    db: Session, normal_user_access_token: str
) -> None:
    # project
    project = create_project(db)
    # point preview
    point_vector_layer: VectorLayerDict = get_geojson_feature_collection("point")
    gdf = gpd.GeoDataFrame.from_features(
        point_vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    point_features = crud.vector_layer.create_with_project(
        db, file_name=point_vector_layer["layer_name"], gdf=gdf, project_id=project.id
    )
    point_preview = create_vector_layer_preview(
        project_id=project.id,
        layer_id=point_features[0].properties["layer_id"],
        features=point_features,
    )
    # line preview
    line_vector_layer: VectorLayerDict = get_geojson_feature_collection("linestring")
    gdf = gpd.GeoDataFrame.from_features(
        line_vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    line_features = crud.vector_layer.create_with_project(
        db, file_name=line_vector_layer["layer_name"], gdf=gdf, project_id=project.id
    )
    line_preview = create_vector_layer_preview(
        project_id=project.id,
        layer_id=line_features[0].properties["layer_id"],
        features=line_features,
    )
    # polygon preview
    polygon_vector_layer: VectorLayerDict = get_geojson_feature_collection("polygon")
    gdf = gpd.GeoDataFrame.from_features(
        polygon_vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    polygon_features = crud.vector_layer.create_with_project(
        db, file_name=polygon_vector_layer["layer_name"], gdf=gdf, project_id=project.id
    )
    polygon_preview = create_vector_layer_preview(
        project_id=project.id,
        layer_id=polygon_features[0].properties["layer_id"],
        features=polygon_features,
    )

    assert os.path.exists(point_preview)
    assert os.path.exists(line_preview)
    assert os.path.exists(polygon_preview)


def test_save_vector_layer_parquet(db: Session) -> None:
    """Test that save_vector_layer_parquet creates valid parquet files."""
    # Create project
    project = create_project(db)

    # Test with Point geometry
    point_vector_layer: VectorLayerDict = get_geojson_feature_collection("point")
    gdf_point = gpd.GeoDataFrame.from_features(
        point_vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    point_features = crud.vector_layer.create_with_project(
        db, file_name=point_vector_layer["layer_name"], gdf=gdf_point, project_id=project.id
    )
    point_layer_id = point_features[0].properties["layer_id"]

    # Generate parquet file
    static_dir = get_static_dir()
    parquet_path = save_vector_layer_parquet(
        project_id=project.id,
        layer_id=point_layer_id,
        gdf=gdf_point,
        static_dir=static_dir,
    )

    # Verify parquet file exists
    assert os.path.exists(parquet_path)
    expected_path = os.path.join(
        settings.TEST_STATIC_DIR,
        "projects",
        str(project.id),
        "vector",
        point_layer_id,
        f"{point_layer_id}.parquet",
    )
    assert parquet_path == expected_path

    # Verify parquet file can be read
    gdf_from_parquet = gpd.read_parquet(parquet_path)
    assert len(gdf_from_parquet) == len(gdf_point)
    assert gdf_from_parquet.crs == gdf_point.crs

    # Test with Polygon geometry
    polygon_vector_layer: VectorLayerDict = get_geojson_feature_collection("polygon")
    gdf_polygon = gpd.GeoDataFrame.from_features(
        polygon_vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    polygon_features = crud.vector_layer.create_with_project(
        db, file_name=polygon_vector_layer["layer_name"], gdf=gdf_polygon, project_id=project.id
    )
    polygon_layer_id = polygon_features[0].properties["layer_id"]

    # Generate parquet file for polygon
    parquet_path_polygon = save_vector_layer_parquet(
        project_id=project.id,
        layer_id=polygon_layer_id,
        gdf=gdf_polygon,
        static_dir=static_dir,
    )

    # Verify polygon parquet file
    assert os.path.exists(parquet_path_polygon)
    gdf_polygon_from_parquet = gpd.read_parquet(parquet_path_polygon)
    assert len(gdf_polygon_from_parquet) == len(gdf_polygon)

    # Test with LineString geometry
    line_vector_layer: VectorLayerDict = get_geojson_feature_collection("linestring")
    gdf_line = gpd.GeoDataFrame.from_features(
        line_vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    line_features = crud.vector_layer.create_with_project(
        db, file_name=line_vector_layer["layer_name"], gdf=gdf_line, project_id=project.id
    )
    line_layer_id = line_features[0].properties["layer_id"]

    # Generate parquet file for line
    parquet_path_line = save_vector_layer_parquet(
        project_id=project.id,
        layer_id=line_layer_id,
        gdf=gdf_line,
        static_dir=static_dir,
    )

    # Verify line parquet file
    assert os.path.exists(parquet_path_line)
    gdf_line_from_parquet = gpd.read_parquet(parquet_path_line)
    assert len(gdf_line_from_parquet) == len(gdf_line)


def test_save_vector_layer_flatgeobuf(db: Session) -> None:
    """Test that save_vector_layer_flatgeobuf creates valid FlatGeobuf files."""
    # Create project
    project = create_project(db)

    # Test with Point geometry
    point_vector_layer: VectorLayerDict = get_geojson_feature_collection("point")
    gdf_point = gpd.GeoDataFrame.from_features(
        point_vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    point_features = crud.vector_layer.create_with_project(
        db, file_name=point_vector_layer["layer_name"], gdf=gdf_point, project_id=project.id
    )
    point_layer_id = point_features[0].properties["layer_id"]

    # Generate FlatGeobuf file
    static_dir = get_static_dir()
    fgb_path = save_vector_layer_flatgeobuf(
        project_id=project.id,
        layer_id=point_layer_id,
        gdf=gdf_point,
        static_dir=static_dir,
    )

    # Verify FlatGeobuf file exists
    assert os.path.exists(fgb_path)
    expected_path = os.path.join(
        settings.TEST_STATIC_DIR,
        "projects",
        str(project.id),
        "vector",
        point_layer_id,
        f"{point_layer_id}.fgb",
    )
    assert fgb_path == expected_path

    # Verify FlatGeobuf file can be read
    gdf_from_fgb = gpd.read_file(fgb_path)
    assert len(gdf_from_fgb) == len(gdf_point)
    assert gdf_from_fgb.crs == gdf_point.crs

    # Test with Polygon geometry
    polygon_vector_layer: VectorLayerDict = get_geojson_feature_collection("polygon")
    gdf_polygon = gpd.GeoDataFrame.from_features(
        polygon_vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    polygon_features = crud.vector_layer.create_with_project(
        db, file_name=polygon_vector_layer["layer_name"], gdf=gdf_polygon, project_id=project.id
    )
    polygon_layer_id = polygon_features[0].properties["layer_id"]

    # Generate FlatGeobuf file for polygon
    fgb_path_polygon = save_vector_layer_flatgeobuf(
        project_id=project.id,
        layer_id=polygon_layer_id,
        gdf=gdf_polygon,
        static_dir=static_dir,
    )

    # Verify polygon FlatGeobuf file
    assert os.path.exists(fgb_path_polygon)
    gdf_polygon_from_fgb = gpd.read_file(fgb_path_polygon)
    assert len(gdf_polygon_from_fgb) == len(gdf_polygon)

    # Test with LineString geometry
    line_vector_layer: VectorLayerDict = get_geojson_feature_collection("linestring")
    gdf_line = gpd.GeoDataFrame.from_features(
        line_vector_layer["geojson"]["features"], crs="EPSG:4326"
    )
    line_features = crud.vector_layer.create_with_project(
        db, file_name=line_vector_layer["layer_name"], gdf=gdf_line, project_id=project.id
    )
    line_layer_id = line_features[0].properties["layer_id"]

    # Generate FlatGeobuf file for line
    fgb_path_line = save_vector_layer_flatgeobuf(
        project_id=project.id,
        layer_id=line_layer_id,
        gdf=gdf_line,
        static_dir=static_dir,
    )

    # Verify line FlatGeobuf file
    assert os.path.exists(fgb_path_line)
    gdf_line_from_fgb = gpd.read_file(fgb_path_line)
    assert len(gdf_line_from_fgb) == len(gdf_line)


def test_parse_vector_parquet_path() -> None:
    """Test that parse_vector_parquet_path correctly parses valid paths and rejects invalid ones."""
    # Test valid path with matching layer_id
    valid_uuid = "fbeb7163-61d0-4588-ade3-0f1ae17159a4"
    valid_layer_id = "57WI4EOFlP4"
    valid_path = f"/static/projects/{valid_uuid}/vector/{valid_layer_id}/{valid_layer_id}.parquet"

    result = parse_vector_parquet_path(valid_path)
    assert result is not None
    assert result[0] == UUID(valid_uuid)
    assert result[1] == valid_layer_id

    # Test path with mismatched layer_id in directory and filename
    mismatched_path = f"/static/projects/{valid_uuid}/vector/{valid_layer_id}/different_id.parquet"
    result = parse_vector_parquet_path(mismatched_path)
    assert result is None

    # Test non-parquet file
    non_parquet_path = f"/static/projects/{valid_uuid}/vector/{valid_layer_id}/preview.png"
    result = parse_vector_parquet_path(non_parquet_path)
    assert result is None

    # Test invalid UUID
    invalid_uuid_path = f"/static/projects/invalid-uuid/vector/{valid_layer_id}/{valid_layer_id}.parquet"
    result = parse_vector_parquet_path(invalid_uuid_path)
    assert result is None

    # Test wrong path structure (missing vector directory)
    wrong_structure = f"/static/projects/{valid_uuid}/data/{valid_layer_id}.parquet"
    result = parse_vector_parquet_path(wrong_structure)
    assert result is None

    # Test path with uppercase UUID (should work due to case-insensitive regex)
    uppercase_uuid = valid_uuid.upper()
    uppercase_path = f"/static/projects/{uppercase_uuid}/vector/{valid_layer_id}/{valid_layer_id}.parquet"
    result = parse_vector_parquet_path(uppercase_path)
    assert result is not None
    assert result[0] == UUID(valid_uuid)  # UUID should normalize to lowercase
    assert result[1] == valid_layer_id


def test_parse_vector_flatgeobuf_path() -> None:
    """Test that parse_vector_flatgeobuf_path correctly parses valid paths and rejects invalid ones."""
    # Test valid path with matching layer_id
    valid_uuid = "fbeb7163-61d0-4588-ade3-0f1ae17159a4"
    valid_layer_id = "57WI4EOFlP4"
    valid_path = f"/static/projects/{valid_uuid}/vector/{valid_layer_id}/{valid_layer_id}.fgb"

    result = parse_vector_flatgeobuf_path(valid_path)
    assert result is not None
    assert result[0] == UUID(valid_uuid)
    assert result[1] == valid_layer_id

    # Test path with mismatched layer_id in directory and filename
    mismatched_path = f"/static/projects/{valid_uuid}/vector/{valid_layer_id}/different_id.fgb"
    result = parse_vector_flatgeobuf_path(mismatched_path)
    assert result is None

    # Test non-FlatGeobuf file
    non_fgb_path = f"/static/projects/{valid_uuid}/vector/{valid_layer_id}/preview.png"
    result = parse_vector_flatgeobuf_path(non_fgb_path)
    assert result is None

    # Test invalid UUID
    invalid_uuid_path = f"/static/projects/invalid-uuid/vector/{valid_layer_id}/{valid_layer_id}.fgb"
    result = parse_vector_flatgeobuf_path(invalid_uuid_path)
    assert result is None

    # Test wrong path structure (missing vector directory)
    wrong_structure = f"/static/projects/{valid_uuid}/data/{valid_layer_id}.fgb"
    result = parse_vector_flatgeobuf_path(wrong_structure)
    assert result is None

    # Test path with uppercase UUID (should work due to case-insensitive regex)
    uppercase_uuid = valid_uuid.upper()
    uppercase_path = f"/static/projects/{uppercase_uuid}/vector/{valid_layer_id}/{valid_layer_id}.fgb"
    result = parse_vector_flatgeobuf_path(uppercase_path)
    assert result is not None
    assert result[0] == UUID(valid_uuid)  # UUID should normalize to lowercase
    assert result[1] == valid_layer_id


def test_parse_vector_parquet_path_security() -> None:
    """Test that parse_vector_parquet_path rejects malicious layer_ids."""
    valid_uuid = "fbeb7163-61d0-4588-ade3-0f1ae17159a4"

    # Test path traversal attempts - should all be rejected
    path_traversal_attempts = [
        f"/static/projects/{valid_uuid}/vector/../../../etc/passwd/file.parquet",
        f"/static/projects/{valid_uuid}/vector/..%2F..%2Fetc/file.parquet",
        f"/static/projects/{valid_uuid}/vector/....//etc/file.parquet",
        f"/static/projects/{valid_uuid}/vector/..\\/etc/file.parquet",
    ]

    for malicious_path in path_traversal_attempts:
        result = parse_vector_parquet_path(malicious_path)
        assert result is None, f"Should reject path traversal: {malicious_path}"

    # Test invalid layer_id formats (not matching base64url pattern)
    invalid_layer_ids = [
        "../../etc/passwd",  # Path traversal
        "layer$$$id",  # Special characters
        "layer<script>",  # HTML injection
        "layer;rm -rf",  # Command injection
        "a" * 100,  # Too long
        "short",  # Too short
        "InvalidLayerID",  # Wrong length (15 chars instead of 11)
        "",  # Empty
    ]

    for invalid_id in invalid_layer_ids:
        malicious_path = f"/static/projects/{valid_uuid}/vector/{invalid_id}/{invalid_id}.parquet"
        result = parse_vector_parquet_path(malicious_path)
        assert result is None, f"Should reject invalid layer_id: {invalid_id}"

    # Test that only valid base64url characters are accepted (11 chars exactly)
    valid_layer_id = "57WI4EOFlP4"  # Valid: 11 chars, base64url alphabet
    valid_path = f"/static/projects/{valid_uuid}/vector/{valid_layer_id}/{valid_layer_id}.parquet"
    result = parse_vector_parquet_path(valid_path)
    assert result is not None, "Should accept valid layer_id"
    assert result[1] == valid_layer_id


def test_parse_vector_flatgeobuf_path_security() -> None:
    """Test that parse_vector_flatgeobuf_path rejects malicious layer_ids."""
    valid_uuid = "fbeb7163-61d0-4588-ade3-0f1ae17159a4"

    # Test path traversal attempts - should all be rejected
    path_traversal_attempts = [
        f"/static/projects/{valid_uuid}/vector/../../../etc/passwd/file.fgb",
        f"/static/projects/{valid_uuid}/vector/..%2F..%2Fetc/file.fgb",
        f"/static/projects/{valid_uuid}/vector/....//etc/file.fgb",
        f"/static/projects/{valid_uuid}/vector/..\\/etc/file.fgb",
    ]

    for malicious_path in path_traversal_attempts:
        result = parse_vector_flatgeobuf_path(malicious_path)
        assert result is None, f"Should reject path traversal: {malicious_path}"

    # Test invalid layer_id formats (not matching base64url pattern)
    invalid_layer_ids = [
        "../../etc/passwd",  # Path traversal
        "layer$$$id",  # Special characters
        "layer<script>",  # HTML injection
        "layer;rm -rf",  # Command injection
        "a" * 100,  # Too long
        "short",  # Too short
        "InvalidLayerID",  # Wrong length (15 chars instead of 11)
        "",  # Empty
    ]

    for invalid_id in invalid_layer_ids:
        malicious_path = f"/static/projects/{valid_uuid}/vector/{invalid_id}/{invalid_id}.fgb"
        result = parse_vector_flatgeobuf_path(malicious_path)
        assert result is None, f"Should reject invalid layer_id: {invalid_id}"

    # Test that only valid base64url characters are accepted (11 chars exactly)
    valid_layer_id = "57WI4EOFlP4"  # Valid: 11 chars, base64url alphabet
    valid_path = f"/static/projects/{valid_uuid}/vector/{valid_layer_id}/{valid_layer_id}.fgb"
    result = parse_vector_flatgeobuf_path(valid_path)
    assert result is not None, "Should accept valid layer_id"
    assert result[1] == valid_layer_id

