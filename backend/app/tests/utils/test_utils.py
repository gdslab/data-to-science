import os
from datetime import datetime, timedelta
from typing import List

import geopandas as gpd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.utils import create_vector_layer_preview
from app.core.config import settings
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
                project.deactivated_at = datetime.now() - timedelta(weeks=3)
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
                flight.deactivated_at = datetime.now() - timedelta(weeks=3)
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
                data_product.deactivated_at = datetime.now() - timedelta(weeks=3)
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
                raw_data.deactivated_at = datetime.now() - timedelta(weeks=3)
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
            start_time=datetime.now() - timedelta(weeks=3),
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
                assert job.start_time > datetime.now() - timedelta(weeks=2)
