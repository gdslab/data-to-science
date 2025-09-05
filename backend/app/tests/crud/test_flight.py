import os
from datetime import date, datetime, timezone

import geopandas as gpd
from geojson_pydantic import FeatureCollection
from sqlalchemy import update
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.flight import PLATFORMS, SENSORS
from app.models.vector_layer import VectorLayer
from app.schemas.data_product import DataProductCreate
from app.schemas.flight import FlightUpdate
from app.schemas.job import State, Status
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight
from app.tests.utils.job import create_job
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user
from app.tests.utils.vector_layers import get_geojson_feature_collection


def test_create_flight(db: Session) -> None:
    pilot = create_user(db)
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    name = "Test Flight"
    acquisition_date = date.today()
    altitude = 100
    side_overlap = 60
    forward_overlap = 75
    flight = create_flight(
        db,
        name=name,
        acquisition_date=acquisition_date,
        altitude=altitude,
        side_overlap=side_overlap,
        forward_overlap=forward_overlap,
        sensor=SENSORS[0],
        platform=PLATFORMS[0],
        project_id=project.id,
        pilot_id=pilot.id,
    )
    assert flight
    assert name == flight.name
    assert acquisition_date == flight.acquisition_date
    assert altitude == flight.altitude
    assert side_overlap == flight.side_overlap
    assert forward_overlap == flight.forward_overlap
    assert SENSORS[0] == flight.sensor
    assert PLATFORMS[0] == flight.platform
    assert project.id == flight.project_id
    assert pilot.id == flight.pilot_id
    assert flight.created_at is not None
    assert flight.updated_at is not None
    assert flight.updated_at >= flight.created_at


def test_get_flight(db: Session) -> None:
    flight = create_flight(db)
    stored_flight = crud.flight.get_flight_by_id(
        db, project_id=flight.project_id, flight_id=flight.id
    )
    assert stored_flight and stored_flight["result"]
    assert flight.name == stored_flight["result"].name
    assert flight.id == stored_flight["result"].id
    assert flight.acquisition_date == stored_flight["result"].acquisition_date
    assert flight.altitude == stored_flight["result"].altitude
    assert flight.side_overlap == stored_flight["result"].side_overlap
    assert flight.forward_overlap == stored_flight["result"].forward_overlap
    assert flight.sensor == stored_flight["result"].sensor
    assert flight.platform == stored_flight["result"].platform
    assert flight.project_id == stored_flight["result"].project_id
    assert flight.pilot_id == stored_flight["result"].pilot_id
    assert stored_flight["result"].created_at is not None
    assert stored_flight["result"].updated_at is not None


def test_get_flights(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    other_project = create_project(db)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=other_project.id)
    upload_dir = settings.TEST_STATIC_DIR
    flights = crud.flight.get_multi_by_project(
        db, project_id=project.id, upload_dir=upload_dir, user_id=user.id
    )
    assert type(flights) is list
    assert len(flights) == 3
    for flight in flights:
        assert flight.project_id == project.id


def test_get_flights_with_raster_data_products(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)
    flight3 = create_flight(db, project_id=project.id)
    # Add raster data product to flight1
    raster_data_product1 = SampleDataProduct(
        db, data_type="ortho", flight=flight1, project=project
    )
    # Add point cloud data product to flight2
    point_cloud_data_product = crud.data_product.create_with_flight(
        db,
        obj_in=DataProductCreate(
            data_type="point_cloud",
            filepath=f"/some/path/to/test.las",
            original_filename="test.las",
        ),
        flight_id=flight2.id,
    )
    upload_dir = settings.TEST_STATIC_DIR
    flights_with_rasters = crud.flight.get_multi_by_project(
        db,
        project_id=project.id,
        upload_dir=upload_dir,
        user_id=user.id,
        has_raster=True,
        include_all=True,
    )
    assert flights_with_rasters
    assert isinstance(flights_with_rasters, list)
    assert len(flights_with_rasters) == 1
    assert flights_with_rasters[0].id == flight1.id


def test_get_flights_excluding_processing_or_failed_data_products(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id)
    data_product1 = SampleDataProduct(
        db, data_type="ortho", project=project, flight=flight, user=user, skip_job=True
    )
    create_job(
        db,
        name="upload-data-product",
        state=State.COMPLETED,
        status=Status.FAILED,
        data_product_id=data_product1.obj.id,
    )
    data_product2 = SampleDataProduct(
        db, data_type="dsm", project=project, flight=flight, user=user, skip_job=True
    )
    create_job(
        db,
        name="upload-data-product",
        state=State.COMPLETED,
        status=Status.SUCCESS,
        data_product_id=data_product2.obj.id,
    )
    data_product3 = SampleDataProduct(
        db, data_type="ortho", project=project, flight=flight, user=user, skip_job=True
    )
    create_job(
        db,
        name="upload-data-product",
        state=State.PENDING,
        status=Status.SUCCESS,
        data_product_id=data_product3.obj.id,
    )
    upload_dir = settings.TEST_STATIC_DIR
    flights = crud.flight.get_multi_by_project(
        db,
        project_id=project.id,
        upload_dir=upload_dir,
        user_id=user.id,
        include_all=False,
    )
    assert type(flights) is list
    assert len(flights) == 1
    assert len(flights[0].data_products) == 1
    assert flights[0].data_products[0].data_type == "dsm"


def test_update_flight(db: Session) -> None:
    flight = create_flight(db, altitude=60, sensor=SENSORS[0])
    original_created_at = flight.created_at
    original_updated_at = flight.updated_at
    flight_in_update = FlightUpdate(altitude=100, sensor=SENSORS[1])
    flight_update = crud.flight.update(db, db_obj=flight, obj_in=flight_in_update)
    assert flight.id == flight_update.id
    assert flight_in_update.altitude == flight_update.altitude
    assert flight_in_update.sensor == flight_update.sensor
    assert flight_update.created_at == original_created_at
    assert flight_update.updated_at > original_updated_at


def test_deactivate_flight(db: Session) -> None:
    flight = create_flight(db)
    flight2 = crud.flight.deactivate(db, flight_id=flight.id)
    flight3 = crud.flight.get(db, id=flight.id)
    assert flight2 and flight3
    assert flight3.id == flight.id
    assert flight3.is_active is False
    assert isinstance(flight3.deactivated_at, datetime)
    assert flight3.deactivated_at.replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    )


def test_deactivate_flight_deactivates_data_products(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)
    flight2 = crud.flight.deactivate(db, flight_id=flight.id)
    flight3 = crud.flight.get(db, id=flight.id)
    assert flight3 and flight3.is_active is False
    upload_dir = settings.TEST_STATIC_DIR
    data_product = crud.data_product.get(db, id=data_product.obj.id)
    assert data_product and data_product.is_active is False


def test_get_deactivated_flight_returns_none(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id)
    crud.flight.deactivate(db, flight_id=flight.id)
    flight2 = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight.id
    )
    assert flight2 and flight2["result"] is None


def test_get_flights_ignores_deactivated_flight(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight_to_deactivate = create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    crud.flight.deactivate(db, flight_id=flight_to_deactivate.id)
    upload_dir = settings.TEST_STATIC_DIR
    flights = crud.flight.get_multi_by_project(
        db, project_id=project.id, upload_dir=upload_dir, user_id=user.id
    )
    assert type(flights) is list
    assert len(flights) == 2


def test_get_flight_for_deactivated_project_returns_none(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id)
    crud.project.deactivate(db, project_id=project.id, user_id=user.id)
    flight2 = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight.id
    )
    assert flight2 and flight2["result"] is None


def test_get_flights_ignores_deactivated_project(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    create_flight(db, project_id=project.id)
    crud.project.deactivate(db, project_id=project.id, user_id=user.id)
    upload_dir = settings.TEST_STATIC_DIR
    flights = crud.flight.get_multi_by_project(
        db, project_id=project.id, upload_dir=upload_dir, user_id=user.id
    )
    assert type(flights) is list
    assert len(flights) == 0


def test_get_flight_ignores_deactivated_data_products(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id)
    data_product1 = SampleDataProduct(db, project=project, flight=flight)
    data_product2 = SampleDataProduct(db, project=project, flight=flight)
    data_product3 = SampleDataProduct(db, project=project, flight=flight)
    crud.data_product.deactivate(db, data_product_id=data_product1.obj.id)
    upload_dir = settings.TEST_STATIC_DIR
    flight = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight.id
    )
    assert flight and flight.get("result")
    assert len(flight.get("result").data_products) == 2


def test_get_flights_ignores_deactivated_data_products(db: Session) -> None:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)

    flight1 = create_flight(db, project_id=project.id)
    flight2 = create_flight(db, project_id=project.id)

    data_f1d1 = SampleDataProduct(db, project=project, flight=flight1)
    data_f2d1 = SampleDataProduct(db, project=project, flight=flight2)
    data_f1d2 = SampleDataProduct(db, project=project, flight=flight1)
    data_f2d2 = SampleDataProduct(db, project=project, flight=flight2)

    upload_dir = settings.TEST_STATIC_DIR
    flights = crud.flight.get_multi_by_project(
        db,
        project_id=project.id,
        upload_dir=upload_dir,
        user_id=user.id,
        include_all=True,
    )
    for flight in flights:
        assert len(flight.data_products) == 2

    crud.data_product.deactivate(db, data_product_id=data_f1d1.obj.id)
    crud.data_product.deactivate(db, data_product_id=data_f2d1.obj.id)

    flights2 = crud.flight.get_multi_by_project(
        db,
        project_id=project.id,
        upload_dir=upload_dir,
        user_id=user.id,
        include_all=True,
    )
    for flight in flights2:
        assert len(flight.data_products) == 1


def test_update_flight_project(db: Session) -> None:
    user = create_user(db)
    # source and destination projects
    src_project = create_project(db, owner_id=user.id)
    dst_project = create_project(db, owner_id=user.id)
    # create flight associated with source project
    flight = create_flight(db, project_id=src_project.id)
    flight2 = create_flight(db, project_id=src_project.id)
    flight3 = create_flight(db, project_id=src_project.id)
    # add data product to flight
    data_product = SampleDataProduct(db, flight=flight)

    # create vector layer and associate it with flight
    geojson = get_geojson_feature_collection("Point")["geojson"]
    fc: FeatureCollection = FeatureCollection(**geojson)
    gdf = gpd.GeoDataFrame.from_features(fc.features, crs="EPSG:4326")
    point_feature = crud.vector_layer.create_with_project(
        db, file_name="test_file.geojson", gdf=gdf, project_id=src_project.id
    )

    update_query = (
        update(VectorLayer)
        .values(flight_id=flight.id)
        .where(VectorLayer.layer_id == point_feature[0].properties["layer_id"])
    )
    with db as session:
        session.execute(update_query)
        session.commit()
    # move flight from source project to destination project
    moved_flight = crud.flight.change_flight_project(
        db, flight_id=flight.id, dst_project_id=dst_project.id
    )
    vector_layer_after_move = crud.vector_layer.get_vector_layer_by_id(
        db, project_id=dst_project.id, layer_id=point_feature[0].properties["layer_id"]
    )
    new_data_product_location = os.path.join(
        settings.TEST_STATIC_DIR,
        "projects",
        str(dst_project.id),
        "flights",
        str(flight.id),
        "data_products",
        str(data_product.obj.id),
        os.path.basename(data_product.obj.filepath),
    )
    upload_dir = settings.TEST_STATIC_DIR
    src_flights = crud.flight.get_multi_by_project(
        db, project_id=src_project.id, upload_dir=upload_dir, user_id=user.id
    )
    upload_dir = settings.TEST_STATIC_DIR
    dst_flights = crud.flight.get_multi_by_project(
        db, project_id=dst_project.id, upload_dir=upload_dir, user_id=user.id
    )
    assert moved_flight.id == flight.id
    assert moved_flight.project_id == dst_project.id
    assert len(moved_flight.data_products) == 1
    assert moved_flight.data_products[0].filepath == new_data_product_location
    assert len(vector_layer_after_move) > 0
    assert vector_layer_after_move[0].properties["project_id"] == str(dst_project.id)
    assert len(src_flights) == 2
    assert len(dst_flights) == 1
