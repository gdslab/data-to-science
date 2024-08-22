import json
import os

import geopandas as gpd
import pytest
from fastapi.encoders import jsonable_encoder
from geojson_pydantic import Feature, FeatureCollection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.schemas.data_product_metadata import (
    DataProductMetadataCreate,
    DataProductMetadataUpdate,
)
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_metadata import create_metadata, get_zonal_statistics
from app.tests.utils.project import create_project
from app.tests.utils.vector_layers import (
    create_vector_layer_with_provided_feature_collection,
)


def test_create_data_product_metadata(db: Session) -> None:
    data_product = SampleDataProduct(db, data_type="dsm")
    bbox_filepath = os.path.join(
        os.sep, "app", "app", "tests", "data", "zones_inside_test_tif.geojson"
    )
    with open(bbox_filepath) as bbox_file:
        # create vector layer record for bbox
        bbox_dict = json.loads(bbox_file.read())

    bbox_feature_collection = FeatureCollection(**bbox_dict)
    project = create_project(db)
    bbox_vector_layer = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=bbox_feature_collection, project_id=project.id
    )
    stats = get_zonal_statistics(data_product.obj.filepath, bbox_feature_collection)
    metadata_in = DataProductMetadataCreate(
        category="zonal",
        properties={"stats": stats[0]},
        vector_layer_id=bbox_vector_layer.features[0].properties["id"],
    )
    metadata = crud.data_product_metadata.create_with_data_product(
        db, obj_in=metadata_in, data_product_id=data_product.obj.id
    )
    assert metadata
    assert metadata.category == "zonal"
    assert metadata.properties["stats"] == stats[0]
    assert metadata.data_product_id == data_product.obj.id
    assert (
        str(metadata.vector_layer_id) == bbox_vector_layer.features[0].properties["id"]
    )


def test_create_data_product_metadata_for_multiple_zones(db: Session) -> None:
    data_product = SampleDataProduct(db, data_type="dsm")
    bbox_filepath = os.path.join(
        os.sep, "app", "app", "tests", "data", "test_bbox_multi.geojson"
    )
    with open(bbox_filepath) as bbox_file:
        # create vector layer record for bbox
        bbox_dict = json.loads(bbox_file.read())

    bbox_feature_collection = FeatureCollection(**bbox_dict)
    project = create_project(db)
    bbox_vector_layer = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=bbox_feature_collection, project_id=project.id
    )
    stats = get_zonal_statistics(data_product.obj.filepath, bbox_feature_collection)
    assert isinstance(stats, list)
    assert len(stats) == 3  # number of features in text_bbox_multi feature collection
    all_metadata = []
    for index, feature in enumerate(bbox_vector_layer.features):
        metadata_in = DataProductMetadataCreate(
            category="zonal",
            properties={"stats": stats[index]},
            vector_layer_id=feature.properties["id"],
        )
        metadata = crud.data_product_metadata.create_with_data_product(
            db, obj_in=metadata_in, data_product_id=data_product.obj.id
        )
        all_metadata.append(metadata)
    assert len(all_metadata) == 3


def test_create_duplicate_zonal_metadata(db: Session) -> None:
    metadata = create_metadata(db, single_feature=True)[0][0]
    # unique constraint should cause integrity error
    with pytest.raises(IntegrityError):
        metadata_duplicate = create_metadata(
            db,
            data_product_id=metadata.data_product_id,
            vector_layer_id=metadata.vector_layer_id,
            single_feature=True,
        )


def test_create_zonal_metadata_with_zone_outside_raster(db: Session) -> None:
    data_product = SampleDataProduct(db, data_type="dsm")
    bbox_filepath = os.path.join(
        os.sep, "app", "app", "tests", "data", "zone_outside_raster.geojson"
    )
    with open(bbox_filepath) as bbox_file:
        # create vector layer record for bbox
        bbox_dict = json.loads(bbox_file.read())

    bbox_feature_collection = FeatureCollection(**bbox_dict)
    project = create_project(db)
    bbox_vector_layer = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=bbox_feature_collection, project_id=project.id
    )
    stats = get_zonal_statistics(data_product.obj.filepath, bbox_feature_collection)
    metadata_in = DataProductMetadataCreate(
        category="zonal",
        properties={"stats": stats[0]},
        vector_layer_id=bbox_vector_layer.features[0].properties["id"],
    )
    metadata = crud.data_product_metadata.create_with_data_product(
        db, obj_in=metadata_in, data_product_id=data_product.obj.id
    )
    assert metadata
    assert metadata.properties["stats"]["max"] is None
    assert metadata.properties["stats"]["min"] is None
    assert metadata.properties["stats"]["mean"] is None
    assert metadata.properties["stats"]["median"] is None
    assert metadata.properties["stats"]["std"] is None
    assert metadata.properties["stats"]["count"] == 0


def test_read_data_product_metadata(db: Session) -> None:
    metadata = create_metadata(db)[0][0]
    metadata_in_db = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=metadata.data_product_id,
        vector_layer_id=metadata.vector_layer_id,
    )
    assert metadata_in_db
    assert isinstance(metadata_in_db, list)
    assert len(metadata_in_db) == 1
    assert metadata_in_db[0].id == metadata.id
    assert metadata_in_db[0].category == metadata.category
    assert metadata_in_db[0].properties == metadata.properties
    assert metadata_in_db[0].data_product_id == metadata.data_product_id
    assert metadata_in_db[0].vector_layer_id == metadata.vector_layer_id


def test_get_zonal_statistics_by_layer_id(db: Session) -> None:
    metadata, layer_id, original_props = create_metadata(db)
    create_metadata(db)
    zonal_statistics = crud.data_product_metadata.get_zonal_statistics_by_layer_id(
        db, data_product_id=metadata[0].data_product_id, layer_id=layer_id
    )
    assert len(metadata) == len(zonal_statistics)
    for stat_key in ["max", "min", "mean", "count", "median", "std"]:
        assert stat_key in zonal_statistics[0].properties["stats"]


def test_get_zonal_statistics_by_layer_id_with_no_original_props(db: Session) -> None:
    metadata, layer_id, original_props = create_metadata(db, no_props=True)
    create_metadata(db)
    zonal_statistics = crud.data_product_metadata.get_zonal_statistics_by_layer_id(
        db, data_product_id=metadata[0].data_product_id, layer_id=layer_id
    )
    assert len(metadata) == len(zonal_statistics)
    for stat_key in ["max", "min", "mean", "count", "median", "std"]:
        assert stat_key in zonal_statistics[0].properties["stats"]


def test_update_data_product_metadata(db: Session) -> None:
    metadata = create_metadata(db)[0][0]
    metadata_in_db = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=metadata.data_product_id,
        vector_layer_id=metadata.vector_layer_id,
    )
    updated_properties = {
        **metadata.properties,
        "min": 9999,
        "max": 9999,
        "mean": 9999,
        "count": 9999,
        "median": 9999,
        "std": 9999,
    }
    metadata_update_in = DataProductMetadataUpdate(properties=updated_properties)
    metadata_updated = crud.data_product_metadata.update(
        db, db_obj=metadata_in_db[0], obj_in=metadata_update_in
    )
    assert metadata_updated
    assert metadata_in_db[0].id == metadata_updated.id
    assert metadata_in_db[0].properties["min"] == updated_properties["min"]
    assert metadata_in_db[0].properties["max"] == updated_properties["max"]
    assert metadata_in_db[0].properties["mean"] == updated_properties["mean"]
    assert metadata_in_db[0].properties["count"] == updated_properties["count"]
    assert metadata_in_db[0].properties["median"] == updated_properties["median"]
    assert metadata_in_db[0].properties["std"] == updated_properties["std"]


def test_delete_data_product_metadata(db: Session) -> None:
    metadata = create_metadata(db)[0][0]
    metadata_removed = crud.data_product_metadata.remove(db, id=metadata.id)
    metadata_get_after_removed = crud.data_product_metadata.get(db, id=metadata.id)
    assert metadata_get_after_removed is None
    assert metadata_removed
    assert metadata_removed.id == metadata.id
