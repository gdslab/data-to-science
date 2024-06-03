import json
import os

import geopandas as gpd
from fastapi.encoders import jsonable_encoder
from geojson_pydantic import FeatureCollection
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
    data_product = SampleDataProduct(db, data_type="ortho")
    bbox_filepath = os.path.join(
        os.sep, "app", "app", "tests", "data", "test_bbox.geojson"
    )
    with open(bbox_filepath) as bbox_file:
        # create vector layer record for bbox
        bbox_dict = json.loads(bbox_file.read())

    bbox_feature_collection = FeatureCollection(**bbox_dict)
    bbox_feature = bbox_feature_collection.features[0]
    project = create_project(db)
    bbox_vector_layer = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=bbox_feature_collection, project_id=project.id
    )
    stats = get_zonal_statistics(data_product.obj.filepath, bbox_feature)
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
    assert metadata.properties == {"stats": stats[0]}
    assert metadata.data_product_id == data_product.obj.id
    assert (
        str(metadata.vector_layer_id) == bbox_vector_layer.features[0].properties["id"]
    )


def test_read_data_product_metadata(db: Session) -> None:
    metadata = create_metadata(db)
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


def test_update_data_product_metadata(db: Session) -> None:
    metadata = create_metadata(db)
    metadata_in_db = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=metadata.data_product_id,
        vector_layer_id=metadata.vector_layer_id,
    )
    updated_stats = {"stats": {"min": 9999, "max": 9999, "mean": 9999, "count": 9999}}
    metadata_update_in = DataProductMetadataUpdate(properties=updated_stats)
    metadata_updated = crud.data_product_metadata.update(
        db, db_obj=metadata_in_db[0], obj_in=metadata_update_in
    )
    assert metadata_updated
    assert metadata_in_db[0].id == metadata_updated.id
    assert metadata_in_db[0].properties == updated_stats


def test_delete_data_product_metadata(db: Session) -> None:
    metadata = create_metadata(db)
    metadata_removed = crud.data_product_metadata.remove(db, id=metadata.id)
    metadata_get_after_removed = crud.data_product_metadata.get(db, id=metadata.id)
    assert metadata_get_after_removed is None
    assert metadata_removed
    assert metadata_removed.id == metadata.id
