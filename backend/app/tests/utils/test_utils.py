import os
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

import geopandas as gpd
from sqlalchemy import select
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
from app.models.data_product import DataProduct
from app.models.flight import Flight
from app.models.job import Job
from app.models.project import Project
from app.models.raw_data import RawData
from app.schemas.job import JobUpdate
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.raw_data import SampleRawData
from app.tests.utils.user import create_user
from app.tests.utils.utils import VectorLayerDict
from app.tests.utils.vector_layers import (
    get_geojson_feature_collection,
)
from app.utils.cleanup.cleanup_data_products_and_raw_data import (
    cleanup_data_products_and_raw_data,
)
from app.utils.cleanup.cleanup_flights import cleanup_flights
from app.utils.cleanup.cleanup_projects import cleanup_projects
from app.utils.cleanup.cleanup_stale_jobs import cleanup_stale_jobs


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


def test_deactivated_project_cleanup(db: Session) -> None:
    user = create_user(db)
    data_product1 = SampleDataProduct(db, user=user)
    SampleDataProduct(db, user=user)
    SampleDataProduct(db, user=user)
    crud.project.deactivate(db, project_id=data_product1.project.id, user_id=user.id)

    select_all_projects_query = select(Project)
    with db as session:
        all_projects = session.scalars(select_all_projects_query).all()
        assert isinstance(all_projects, List)
        assert len(all_projects) == 3
        for project in all_projects:
            if project.id == data_product1.project.id:
                project_dir = os.path.join(
                    settings.TEST_STATIC_DIR, "projects", str(project.id)
                )
                # confirm project is deactivated and files still exist
                assert project.is_active is False
                assert os.path.isdir(project_dir)
                # set deactivated_at date to more than two weeks ago
                project.deactivated_at = datetime.now(tz=timezone.utc) - timedelta(
                    weeks=3
                )
                session.commit()
                # run cleanup script
                cleanup_projects(db)
                # verify project directory has been removed
                assert not os.path.isdir(project_dir)
                project_in_db = session.scalar(
                    select(Project).where(Project.id == project.id)
                )
                assert project_in_db is None
                # verify flight and data product also removed from db
                flight_in_db = session.scalar(
                    select(Flight).where(Flight.id == data_product1.flight.id)
                )
                assert flight_in_db is None
                data_product_in_db = session.scalar(
                    select(DataProduct).where(DataProduct.id == data_product1.obj.id)
                )
                assert data_product_in_db is None
            else:
                assert project.is_active is True


def test_deactivated_flight_cleanup(db: Session) -> None:
    user = create_user(db)
    data_product1 = SampleDataProduct(db, user=user)
    SampleDataProduct(db, user=user)
    SampleDataProduct(db, user=user)
    crud.flight.deactivate(db, flight_id=data_product1.flight.id)

    select_all_flights_query = select(Flight)
    with db as session:
        all_flights = session.scalars(select_all_flights_query).unique().all()
        assert isinstance(all_flights, List)
        assert len(all_flights) == 3
        for flight in all_flights:
            if flight.id == data_product1.flight.id:
                flight_dir = os.path.join(
                    settings.TEST_STATIC_DIR,
                    "projects",
                    str(data_product1.project.id),
                    "flights",
                    str(flight.id),
                )
                # confirm flight is deactivated and files still exist
                assert flight.is_active is False
                assert os.path.isdir(flight_dir)
                # set deactivated_at date to more than two weeks ago
                flight.deactivated_at = datetime.now(tz=timezone.utc) - timedelta(
                    weeks=3
                )
                session.commit()
                # run cleanup script
                cleanup_flights(db)
                # verify flight directory has been removed
                assert not os.path.isdir(flight_dir)
                flight_in_db = session.scalar(
                    select(Flight).where(Flight.id == flight.id)
                )
                assert flight_in_db is None
                # verify data product also removed from db
                data_product_in_db = session.scalar(
                    select(DataProduct).where(DataProduct.id == data_product1.obj.id)
                )
                assert data_product_in_db is None
            else:
                assert flight.is_active is True


def test_deactivated_data_product_cleanup(db: Session) -> None:
    user = create_user(db)
    data_product1 = SampleDataProduct(db, user=user)
    SampleDataProduct(db, user=user)
    SampleDataProduct(db, user=user)
    raw_data1 = SampleRawData(db, user=user)
    SampleRawData(db, user=user)
    SampleRawData(db, user=user)
    crud.data_product.deactivate(db, data_product_id=data_product1.obj.id)
    crud.raw_data.deactivate(db, raw_data_id=raw_data1.obj.id)

    select_all_data_products_query = select(DataProduct)
    with db as session:
        all_data_products = session.scalars(select_all_data_products_query).all()
        assert isinstance(all_data_products, List)
        assert len(all_data_products) == 3
        for data_product in all_data_products:
            if data_product.id == data_product1.obj.id:
                data_product_dir = os.path.join(
                    settings.TEST_STATIC_DIR,
                    "projects",
                    str(data_product1.project.id),
                    "flights",
                    str(data_product1.flight.id),
                    "data_products",
                    str(data_product1.obj.id),
                )
                # confirm data product is deactivated and files still exist
                assert data_product.is_active is False
                assert os.path.isdir(data_product_dir)
                # set deactivated_at date to more than two weeks ago
                data_product.deactivated_at = datetime.now(tz=timezone.utc) - timedelta(
                    weeks=3
                )
                session.commit()
                # run cleanup script
                cleanup_data_products_and_raw_data(db)
                # verify data product removed from db
                data_product_in_db = session.scalar(
                    select(DataProduct).where(DataProduct.id == data_product1.obj.id)
                )
                assert data_product_in_db is None
            else:
                assert data_product.is_active is True

    select_all_raw_data_query = select(RawData)
    with db as session:
        all_raw_data = session.scalars(select_all_raw_data_query).all()
        assert isinstance(all_raw_data, List)
        assert len(all_raw_data) == 3
        for raw_data in all_raw_data:
            if raw_data.id == raw_data1.obj.id:
                raw_data_dir = os.path.join(
                    settings.TEST_STATIC_DIR,
                    "projects",
                    str(raw_data1.project.id),
                    "flights",
                    str(raw_data1.flight.id),
                    "raw_data",
                    str(raw_data1.obj.id),
                )
                # confirm raw data is deactivated and files still exist
                assert raw_data.is_active is False
                assert os.path.isdir(raw_data_dir)
                # set deactivated_at date to more than two weeks ago
                raw_data.deactivated_at = datetime.now(tz=timezone.utc) - timedelta(
                    weeks=3
                )
                session.commit()
                # run cleanup script
                cleanup_data_products_and_raw_data(db)
                # verify raw data removed from db
                raw_data_in_db = session.scalar(
                    select(RawData).where(RawData.id == raw_data1.obj.id)
                )
                assert raw_data_in_db is None
            else:
                assert raw_data.is_active is True


def test_stale_job_cleanup(db: Session) -> None:
    user = create_user(db)
    data_product1 = SampleDataProduct(db, user=user)
    SampleDataProduct(db, user=user)
    SampleDataProduct(db, user=user)
    crud.job.update(
        db,
        db_obj=data_product1.job,
        obj_in=JobUpdate(
            name="upload-data-product",
            start_time=datetime.now(tz=timezone.utc) - timedelta(weeks=3),
        ),
    )

    select_all_jobs = select(Job)
    with db as session:
        all_jobs = session.scalars(select_all_jobs).all()
        assert isinstance(all_jobs, List)
        assert len(all_jobs) == 3
        for job in all_jobs:
            if job.id == data_product1.job.id:
                data_product_dir = os.path.join(
                    settings.TEST_STATIC_DIR,
                    "projects",
                    str(data_product1.project.id),
                    "flights",
                    str(data_product1.flight.id),
                    "data_products",
                    str(data_product1.obj.id),
                )
                # confirm data product is deactivated and files still exist
                assert os.path.isdir(data_product_dir)
                # run cleanup script
                cleanup_stale_jobs(db)
                # verify data product directory removed
                assert not os.path.isdir(data_product_dir)
                job_in_db = session.scalar(select(Job).where(Job.id == job.id))
                assert job_in_db is None
                data_product_in_db = session.scalar(
                    select(DataProduct).where(DataProduct.id == data_product1.obj.id)
                )
                assert data_product_in_db is None
            else:
                assert job.start_time.replace(tzinfo=timezone.utc) > datetime.now(
                    tz=timezone.utc
                ) - timedelta(weeks=2)
