"""Tests for the toolbox Celery tasks (zonal statistics and tool runs)."""

from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from fastapi.encoders import jsonable_encoder
from geojson_pydantic import FeatureCollection
from rasterio.transform import from_bounds
from rasterio.warp import transform_bounds
from rasterstats import zonal_stats
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.utils import get_data_product_dir
from app.schemas.job import Status
from app.tasks.toolbox_tasks import (
    calculate_bulk_zonal_statistics,
    compute_zonal_statistics,
    run_toolbox,
)
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.data_product_metadata import get_zonal_feature_collection
from app.tests.utils.vector_layers import (
    create_vector_layer_with_provided_feature_collection,
)
from app.utils.job_manager import JobManager

REQUIRED_STATS = {"count", "min", "max", "mean", "median", "std"}


def create_zonal_vector_layer(db: Session, project_id) -> FeatureCollection:
    zones = get_zonal_feature_collection()
    assert isinstance(zones, FeatureCollection)
    return create_vector_layer_with_provided_feature_collection(
        db, feature_collection=zones, project_id=project_id
    )


def outside_polygon_feature(raster_path: str) -> dict:
    """Return a GeoJSON polygon feature that lies entirely to the left of the
    raster's extent (in EPSG:4326), so it overlaps no valid raster pixels.
    """
    with rasterio.open(raster_path) as src:
        minx, miny, maxx, maxy = transform_bounds(src.crs, "EPSG:4326", *src.bounds)
    width = maxx - minx
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [minx - 2 * width, miny],
                    [minx - width, miny],
                    [minx - width, maxy],
                    [minx - 2 * width, maxy],
                    [minx - 2 * width, miny],
                ]
            ],
        },
        "properties": {},
    }


def test_calculate_bulk_zonal_statistics(db: Session) -> None:
    data_product = SampleDataProduct(db, data_type="dsm")
    vector_layer = create_zonal_vector_layer(db, data_product.project.id)
    layer_id = vector_layer.features[0].properties["layer_id"]
    fc_dict = jsonable_encoder(vector_layer.__dict__)
    job = JobManager(
        data_product_id=data_product.obj.id,
        job_name="zonal",
        extra={"layer_id": layer_id},
        db=db,
    )

    with patch("app.tasks.toolbox_tasks.get_db", side_effect=lambda: iter([db])):
        stats = calculate_bulk_zonal_statistics(
            data_product.obj.filepath, data_product.obj.id, fc_dict, job.job_id
        )

    assert len(stats) == len(vector_layer.features)
    # metadata record created for each zone feature
    for feature in vector_layer.features:
        metadata = crud.data_product_metadata.get_by_data_product(
            db,
            category="zonal",
            data_product_id=data_product.obj.id,
            vector_layer_feature_id=feature.properties["feature_id"],
        )
        assert len(metadata) == 1
        assert REQUIRED_STATS.issubset(metadata[0].properties["stats"].keys())

    job_in_db = crud.job.get(db, id=job.job_id)
    assert job_in_db is not None
    assert job_in_db.status == Status.SUCCESS
    # layer id passed at job creation must be preserved
    assert job_in_db.extra["layer_id"] == layer_id
    # every zone overlaps the raster, so the summary reports full coverage
    assert job_in_db.extra["zones_total"] == len(vector_layer.features)
    assert job_in_db.extra["zones_with_data"] == len(vector_layer.features)
    # task must not create a second (orphaned) job for the same run
    jobs = crud.job.get_multi_by_data_product(
        db, data_product_id=data_product.obj.id, job_name="zonal"
    )
    assert len(jobs) == 1


def test_calculate_bulk_zonal_statistics_updates_existing_metadata(
    db: Session,
) -> None:
    data_product = SampleDataProduct(db, data_type="dsm")
    vector_layer = create_zonal_vector_layer(db, data_product.project.id)
    fc_dict = jsonable_encoder(vector_layer.__dict__)

    for _ in range(2):
        job = JobManager(data_product_id=data_product.obj.id, job_name="zonal", db=db)
        with patch("app.tasks.toolbox_tasks.get_db", side_effect=lambda: iter([db])):
            stats = calculate_bulk_zonal_statistics(
                data_product.obj.filepath, data_product.obj.id, fc_dict, job.job_id
            )
        assert len(stats) == len(vector_layer.features)
        job_in_db = crud.job.get(db, id=job.job_id)
        assert job_in_db is not None
        assert job_in_db.status == Status.SUCCESS

    # second run must update metadata in place, not duplicate it
    for feature in vector_layer.features:
        metadata = crud.data_product_metadata.get_by_data_product(
            db,
            category="zonal",
            data_product_id=data_product.obj.id,
            vector_layer_feature_id=feature.properties["feature_id"],
        )
        assert len(metadata) == 1


def test_calculate_bulk_zonal_statistics_failure_marks_job_failed(
    db: Session,
) -> None:
    data_product = SampleDataProduct(db, data_type="dsm")
    vector_layer = create_zonal_vector_layer(db, data_product.project.id)
    fc_dict = jsonable_encoder(vector_layer.__dict__)
    job = JobManager(
        data_product_id=data_product.obj.id,
        job_name="zonal",
        extra={"layer_id": "abc12345"},
        db=db,
    )

    with patch("app.tasks.toolbox_tasks.get_db", side_effect=lambda: iter([db])):
        stats = calculate_bulk_zonal_statistics(
            "/nonexistent/raster.tif", data_product.obj.id, fc_dict, job.job_id
        )

    assert stats == []
    job_in_db = crud.job.get(db, id=job.job_id)
    assert job_in_db is not None
    assert job_in_db.status == Status.FAILED
    # failure reason recorded without clobbering existing extra
    assert "detail" in job_in_db.extra
    assert job_in_db.extra["layer_id"] == "abc12345"


def test_compute_zonal_statistics_with_no_features(db: Session) -> None:
    data_product = SampleDataProduct(db, data_type="dsm")
    assert compute_zonal_statistics(data_product.obj.filepath, {"features": []}) == []


def test_compute_zonal_statistics_with_zone_extending_past_raster_edge(
    db: Session,
) -> None:
    """Stats for a zone must not change when another zone in the same
    collection pushes the read window beyond the raster's extent.
    """
    data_product = SampleDataProduct(db, data_type="dsm")
    raster_path = data_product.obj.filepath
    inside_feature = get_zonal_feature_collection(single_feature=True).model_dump()

    # polygon extending well past the raster's left edge (EPSG:4326)
    with rasterio.open(raster_path) as src:
        src_crs = src.crs
        minx, miny, maxx, maxy = transform_bounds(src.crs, "EPSG:4326", *src.bounds)
    width = maxx - minx
    outside_feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [minx - width, miny],
                    [minx + 0.25 * width, miny],
                    [minx + 0.25 * width, maxy],
                    [minx - width, maxy],
                    [minx - width, miny],
                ]
            ],
        },
        "properties": {},
    }

    # ground truth: rasterstats run against the full raster, no windowing
    zones = gpd.GeoDataFrame.from_features([inside_feature], crs="EPSG:4326").to_crs(
        src_crs
    )
    truth = zonal_stats(zones, raster_path, stats="count min max mean median std")[0]

    expected = compute_zonal_statistics(raster_path, {"features": [inside_feature]})
    actual = compute_zonal_statistics(
        raster_path, {"features": [inside_feature, outside_feature]}
    )

    assert len(expected) == 1
    assert len(actual) == 2
    for stat in REQUIRED_STATS:
        assert expected[0][stat] == pytest.approx(truth[stat])
        assert actual[0][stat] == pytest.approx(truth[stat])


def test_compute_zonal_statistics_with_unsigned_raster_without_nodata(
    tmp_path: Path,
) -> None:
    """A raster whose dtype cannot represent the -999 fallback sentinel
    (e.g., uint8 without a nodata value) must still produce correct stats
    for a zone extending past the raster's edge.
    """
    raster_path = str(tmp_path / "uint8.tif")
    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_bounds(0.0, 0.0, 1.0, 1.0, 10, 10),
    ) as dst:
        dst.write(np.full((10, 10), 100, dtype="uint8"), 1)

    # zone covering the left half of the raster and extending past its edge
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [[-0.5, 0.0], [0.5, 0.0], [0.5, 1.0], [-0.5, 1.0], [-0.5, 0.0]]
            ],
        },
        "properties": {},
    }

    stats = compute_zonal_statistics(raster_path, {"features": [feature]})

    assert len(stats) == 1
    # only the 50 in-raster pixels count; boundless fill pixels are nodata
    assert stats[0]["count"] == 50
    assert stats[0]["min"] == 100
    assert stats[0]["max"] == 100


def test_calculate_bulk_zonal_statistics_all_zones_outside_raster(
    db: Session,
) -> None:
    """When no zone overlaps the raster, the job still succeeds but the
    summary reports zero zones with data and nothing is persisted.
    """
    data_product = SampleDataProduct(db, data_type="dsm")
    outside_fc = FeatureCollection(
        type="FeatureCollection",
        features=[
            outside_polygon_feature(data_product.obj.filepath),
            outside_polygon_feature(data_product.obj.filepath),
        ],
    )
    vector_layer = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=outside_fc, project_id=data_product.project.id
    )
    layer_id = vector_layer.features[0].properties["layer_id"]
    fc_dict = jsonable_encoder(vector_layer.__dict__)
    job = JobManager(
        data_product_id=data_product.obj.id,
        job_name="zonal",
        extra={"layer_id": layer_id},
        db=db,
    )

    with patch("app.tasks.toolbox_tasks.get_db", side_effect=lambda: iter([db])):
        calculate_bulk_zonal_statistics(
            data_product.obj.filepath, data_product.obj.id, fc_dict, job.job_id
        )

    job_in_db = crud.job.get(db, id=job.job_id)
    assert job_in_db is not None
    assert job_in_db.status == Status.SUCCESS
    assert job_in_db.extra["layer_id"] == layer_id
    assert job_in_db.extra["zones_total"] == len(vector_layer.features)
    assert job_in_db.extra["zones_with_data"] == 0
    # no empty-zone metadata should be persisted
    for feature in vector_layer.features:
        metadata = crud.data_product_metadata.get_by_data_product(
            db,
            category="zonal",
            data_product_id=data_product.obj.id,
            vector_layer_feature_id=feature.properties["feature_id"],
        )
        assert len(metadata) == 0


def test_calculate_bulk_zonal_statistics_partial_overlap(db: Session) -> None:
    """A run where only some zones overlap the raster persists metadata for
    the overlapping zones only and reports the partial count.
    """
    data_product = SampleDataProduct(db, data_type="dsm")
    inside_feature = get_zonal_feature_collection(single_feature=True).model_dump()
    mixed_fc = FeatureCollection(
        type="FeatureCollection",
        features=[
            inside_feature,
            outside_polygon_feature(data_product.obj.filepath),
        ],
    )
    vector_layer = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=mixed_fc, project_id=data_product.project.id
    )
    fc_dict = jsonable_encoder(vector_layer.__dict__)
    job = JobManager(data_product_id=data_product.obj.id, job_name="zonal", db=db)

    with patch("app.tasks.toolbox_tasks.get_db", side_effect=lambda: iter([db])):
        calculate_bulk_zonal_statistics(
            data_product.obj.filepath, data_product.obj.id, fc_dict, job.job_id
        )

    job_in_db = crud.job.get(db, id=job.job_id)
    assert job_in_db is not None
    assert job_in_db.status == Status.SUCCESS
    assert job_in_db.extra["zones_total"] == 2
    assert job_in_db.extra["zones_with_data"] == 1

    # metadata persisted for the inside zone, absent for the outside zone
    inside_metadata = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=data_product.obj.id,
        vector_layer_feature_id=vector_layer.features[0].properties["feature_id"],
    )
    outside_metadata = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=data_product.obj.id,
        vector_layer_feature_id=vector_layer.features[1].properties["feature_id"],
    )
    assert len(inside_metadata) == 1
    assert len(outside_metadata) == 0


def test_calculate_bulk_zonal_statistics_removes_stale_empty_metadata(
    db: Session,
) -> None:
    """A zone that no longer overlaps the raster has its previously stored
    stats removed rather than left behind to poison the download endpoint.
    """
    data_product = SampleDataProduct(db, data_type="dsm")
    outside_fc = FeatureCollection(
        type="FeatureCollection",
        features=[outside_polygon_feature(data_product.obj.filepath)],
    )
    vector_layer = create_vector_layer_with_provided_feature_collection(
        db, feature_collection=outside_fc, project_id=data_product.project.id
    )
    feature_id = vector_layer.features[0].properties["feature_id"]
    # pre-seed a stale zonal metadata row for the (now-outside) zone
    crud.data_product_metadata.create_with_data_product(
        db,
        obj_in=schemas.DataProductMetadataCreate(
            category="zonal",
            properties={"stats": {"count": 5, "min": 1, "max": 2}},
            vector_layer_feature_id=feature_id,
        ),
        data_product_id=data_product.obj.id,
    )
    fc_dict = jsonable_encoder(vector_layer.__dict__)
    job = JobManager(data_product_id=data_product.obj.id, job_name="zonal", db=db)

    with patch("app.tasks.toolbox_tasks.get_db", side_effect=lambda: iter([db])):
        calculate_bulk_zonal_statistics(
            data_product.obj.filepath, data_product.obj.id, fc_dict, job.job_id
        )

    stale_metadata = crud.data_product_metadata.get_by_data_product(
        db,
        category="zonal",
        data_product_id=data_product.obj.id,
        vector_layer_feature_id=feature_id,
    )
    assert len(stale_metadata) == 0


def test_run_toolbox_records_file_size_on_output(db: Session) -> None:
    """Tool outputs must persist file_size for per-user data usage reporting."""
    source = SampleDataProduct(db, data_type="ortho", multispectral=True)
    # Output record is created the same way the toolbox endpoint creates it.
    exg_data_product = crud.data_product.create_with_flight(
        db,
        obj_in=schemas.DataProductCreate(
            data_type="ExG",
            filepath="null",
            original_filename=source.obj.original_filename,
        ),
        flight_id=source.flight.id,
    )
    out_raster = (
        get_data_product_dir(
            str(source.project.id), str(source.flight.id), str(exg_data_product.id)
        )
        / "exg.tif"
    )

    # The task builds its own JobManager session, so point that at the test db too.
    with (
        patch("app.tasks.toolbox_tasks.get_db", side_effect=lambda: iter([db])),
        patch("app.utils.job_manager.get_db", side_effect=lambda: iter([db])),
    ):
        run_toolbox(
            "exg",
            source.obj.filepath,
            str(out_raster),
            {"red_band_idx": 3, "green_band_idx": 2, "blue_band_idx": 1},
            exg_data_product.id,
            source.user.id,
        )

    updated = crud.data_product.get(db, id=exg_data_product.id)
    assert updated is not None
    assert updated.is_initial_processing_completed
    assert updated.file_size is not None
    assert updated.file_size > 0
