import os
from uuid import uuid4
from unittest.mock import patch

from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.tasks.stac_tasks import (
    _rollback_s3_uploads,
    _upload_to_s3_and_rewrite_hrefs,
)
from app.tests.conftest import pytest_requires_stac
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight
from app.tests.utils.project import create_project
from app.tests.utils.raw_data import SampleRawData


def _generate_items(db: Session, project_id, include_raw_data_links=None):
    """Helper that runs STACGenerator and returns (items, flights)."""
    from app.utils.stac.STACGenerator import STACGenerator

    sg = STACGenerator(
        db,
        project_id=project_id,
        include_raw_data_links=include_raw_data_links,
    )
    return sg.items, sg.flights


@pytest_requires_stac
def test_upload_to_s3_uploads_new_files_and_rewrites_asset_hrefs(
    db: Session, monkeypatch
):
    """Happy path: untouched data products get uploaded, s3_url persisted, asset href rewritten."""
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    dp = SampleDataProduct(db, project=project, flight=flight)

    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "my-bucket")
    monkeypatch.setattr(settings, "AWS_S3_REGION", "us-east-1")

    items, flights = _generate_items(db, project.id)
    assert len(items) == 1

    fake_url = "https://my-bucket.s3.us-east-1.amazonaws.com/d2s/host/file.tif"
    with patch(
        "app.tasks.stac_tasks.upload_file_to_s3", return_value=fake_url
    ) as mock_upload:
        uploaded_keys = _upload_to_s3_and_rewrite_hrefs(
            db, items, flights, include_raw_data_links=None
        )

    # One upload happened, one key returned
    assert mock_upload.call_count == 1
    assert len(uploaded_keys) == 1

    # Asset href rewritten on the item
    item = items[0]
    assert item.assets[item.id].href == fake_url

    # s3_url persisted to DB
    refreshed = crud.data_product.get(db, id=dp.obj.id)
    assert refreshed is not None
    assert refreshed.s3_url == fake_url


@pytest_requires_stac
def test_upload_to_s3_is_idempotent_when_already_uploaded(db: Session, monkeypatch):
    """If dp.s3_url is already set, skip the upload but still rewrite the href."""
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    dp = SampleDataProduct(db, project=project, flight=flight)

    existing_url = "https://my-bucket.s3.us-east-1.amazonaws.com/d2s/host/already.tif"
    crud.data_product.update_s3_url(db, data_product_id=dp.obj.id, s3_url=existing_url)

    items, flights = _generate_items(db, project.id)

    with patch("app.tasks.stac_tasks.upload_file_to_s3") as mock_upload:
        uploaded_keys = _upload_to_s3_and_rewrite_hrefs(
            db, items, flights, include_raw_data_links=None
        )

    mock_upload.assert_not_called()
    assert uploaded_keys == []
    item = items[0]
    assert item.assets[item.id].href == existing_url


@pytest_requires_stac
def test_upload_to_s3_rewrites_external_viewer_link(db: Session, monkeypatch):
    """When EXTERNAL_VIEWER_URL is set, the 'external' link target is rewritten with the S3 URL."""
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    SampleDataProduct(db, project=project, flight=flight)

    monkeypatch.setattr(settings, "EXTERNAL_VIEWER_URL", "https://viewer.example.com")

    items, flights = _generate_items(db, project.id)
    item = items[0]
    external_links = [link for link in item.links if link.rel == "external"]
    assert external_links, (
        "STACGenerator must add an external link when EXTERNAL_VIEWER_URL is set; "
        "without one, the rewrite branch under test is dead code."
    )

    fake_url = "https://my-bucket.s3.us-east-1.amazonaws.com/d2s/host/file.tif"
    with patch("app.tasks.stac_tasks.upload_file_to_s3", return_value=fake_url):
        _upload_to_s3_and_rewrite_hrefs(
            db, items, flights, include_raw_data_links=None
        )

    rewritten = [link for link in item.links if link.rel == "external"][0]
    assert rewritten.target == f"https://viewer.example.com?url={fake_url}"


@pytest_requires_stac
def test_upload_to_s3_uploads_raw_data_when_derived_from_present(
    db: Session, monkeypatch
):
    """When include_raw_data_links names an item, raw data for its flight gets uploaded
    and derived_from links rewritten."""
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    dp = SampleDataProduct(db, project=project, flight=flight)
    raw = SampleRawData(db, project=project, flight=flight)

    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "my-bucket")

    items, flights = _generate_items(
        db, project.id, include_raw_data_links=[str(dp.obj.id)]
    )

    fake_dp_url = "https://my-bucket.s3.us-east-1.amazonaws.com/d2s/host/dp.tif"
    fake_raw_url = "https://my-bucket.s3.us-east-1.amazonaws.com/d2s/host/raw.zip"

    # Return the data product URL on the first call, raw data URL on the second
    with patch(
        "app.tasks.stac_tasks.upload_file_to_s3",
        side_effect=[fake_dp_url, fake_raw_url],
    ) as mock_upload:
        uploaded_keys = _upload_to_s3_and_rewrite_hrefs(
            db, items, flights, include_raw_data_links=[str(dp.obj.id)]
        )

    assert mock_upload.call_count == 2
    assert len(uploaded_keys) == 2

    # Raw data row got s3_url set
    refreshed_raw = crud.raw_data.get(db, id=raw.obj.id)
    assert refreshed_raw is not None
    assert refreshed_raw.s3_url == fake_raw_url

    # derived_from link on the item now points at the S3 URL
    item = items[0]
    derived_links = [link for link in item.links if link.rel == "derived_from"]
    assert any(link.target == fake_raw_url for link in derived_links)


@pytest_requires_stac
def test_upload_to_s3_skips_items_with_no_matching_data_product(
    db: Session, monkeypatch, caplog
):
    """Synthetic items whose id does not match any data product are skipped, not crashed."""
    from pystac import Item
    from datetime import datetime, timezone

    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    SampleDataProduct(db, project=project, flight=flight)

    items, flights = _generate_items(db, project.id)
    # Inject a stray item with a bogus id
    items.append(
        Item(
            id="not-a-real-data-product",
            geometry={"type": "Point", "coordinates": [0, 0]},
            bbox=[0, 0, 0, 0],
            datetime=datetime.now(tz=timezone.utc),
            properties={},
        )
    )

    with patch(
        "app.tasks.stac_tasks.upload_file_to_s3", return_value="https://x"
    ) as mock_upload:
        with caplog.at_level("WARNING"):
            uploaded_keys = _upload_to_s3_and_rewrite_hrefs(
                db, items, flights, include_raw_data_links=None
            )

    # Only the real data product gets uploaded; the stray item triggers a warning
    assert mock_upload.call_count == 1
    assert len(uploaded_keys) == 1
    assert any("not-a-real-data-product" in rec.message for rec in caplog.records)


@pytest_requires_stac
def test_rollback_deletes_uploaded_keys_and_clears_columns(db: Session):
    """Rollback removes uploaded S3 objects and nulls s3_url on data products and raw data."""
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    dp = SampleDataProduct(db, project=project, flight=flight)
    raw = SampleRawData(db, project=project, flight=flight)

    crud.data_product.update_s3_url(
        db, data_product_id=dp.obj.id, s3_url="https://x/dp"
    )
    crud.raw_data.update_s3_url(db, raw_data_id=raw.obj.id, s3_url="https://x/raw")

    with patch(
        "app.tasks.stac_tasks.delete_s3_objects", return_value=True
    ) as mock_delete:
        _rollback_s3_uploads(db, project.id, ["k1", "k2"])

    mock_delete.assert_called_once_with(["k1", "k2"])

    refreshed_dp = crud.data_product.get(db, id=dp.obj.id)
    refreshed_raw = crud.raw_data.get(db, id=raw.obj.id)
    assert refreshed_dp.s3_url is None
    assert refreshed_raw.s3_url is None


@pytest_requires_stac
def test_rollback_with_empty_key_list_skips_s3_call_but_clears_db(db: Session):
    """If no uploads happened, the rollback still clears any stale s3_url columns."""
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    dp = SampleDataProduct(db, project=project, flight=flight)
    crud.data_product.update_s3_url(
        db, data_product_id=dp.obj.id, s3_url="https://stale"
    )

    with patch("app.tasks.stac_tasks.delete_s3_objects") as mock_delete:
        _rollback_s3_uploads(db, project.id, [])

    mock_delete.assert_not_called()
    assert crud.data_product.get(db, id=dp.obj.id).s3_url is None


def test_rollback_swallows_exceptions(db: Session):
    """Rollback must never raise — failures only log."""
    with patch(
        "app.tasks.stac_tasks.crud.data_product.clear_s3_urls_for_project",
        side_effect=RuntimeError("boom"),
    ), patch("app.tasks.stac_tasks.delete_s3_objects"):
        # Should not raise even though clear_s3_urls_for_project blew up
        _rollback_s3_uploads(db, uuid4(), ["k1"])
