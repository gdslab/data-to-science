"""Unit tests for Change 1 (CH01): Dataset Versioning and Lineage Tracking."""

import os
import sys
import uuid
from unittest.mock import MagicMock

# Ensure evolved code directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.crud.crud_data_product_version import (
    CRUDDataProductVersion,
)
from app.models.data_product_version import (
    DataProductVersion,
)


class MockDataProduct:
    def __init__(self, id=None):
        self.id = id or uuid.uuid4()
        self.filepath = "/static/projects/p1/flights/f1/ortho_v1.tif"
        self.original_filename = "ortho_v1.tif"
        self.file_size = 104857600
        self.stac_properties = {"proj:epsg": 4326}
        self.bbox = [-86.9, 40.4, -86.8, 40.5]
        self.crs = {"epsg": 4326}
        self.resolution = {"x": 0.05, "y": 0.05}


def test_data_product_version_entity_instantiation():
    """Verify DataProductVersion attributes and Memento snapshot integrity."""
    prod_id = uuid.uuid4()
    parent_id = uuid.uuid4()
    version = DataProductVersion(
        data_product_id=prod_id,
        version_number="1.0.0",
        commit_message="Initial orthomosaic generation",
        parent_version_id=parent_id,
        filepath="/static/data/ortho.tif",
        original_filename="ortho.tif",
        file_size=50000000,
        bbox=[-86.9, 40.4, -86.8, 40.5],
        crs={"epsg": 4326},
        resolution={"x": 0.02, "y": 0.02},
        is_current=True,
    )

    assert version.data_product_id == prod_id
    assert version.version_number == "1.0.0"
    assert version.parent_version_id == parent_id
    assert version.is_current is True
    assert version.bbox == [-86.9, 40.4, -86.8, 40.5]


def test_create_snapshot_lineage():
    """Verify create_snapshot creates parent-child lineage and updates active status."""
    mock_db = MagicMock()
    crud_version = CRUDDataProductVersion(DataProductVersion)

    product = MockDataProduct()
    
    # Mock database session methods
    mock_session = MagicMock()
    mock_db.__enter__.return_value = mock_session
    mock_session.scalars.return_value.first.return_value = None  # First version has no parent

    v1 = crud_version.create_snapshot(
        mock_db,
        data_product=product,
        version_number="1.0.0",
        commit_message="Initial flight processing",
    )

    assert v1.version_number == "1.0.0"
    assert v1.is_current is True
    assert v1.parent_version_id is None
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_checkout_version_rollback():
    """Verify checkout_version sets target version as current and synchronizes metadata."""
    mock_db = MagicMock()
    crud_version = CRUDDataProductVersion(DataProductVersion)

    prod_id = uuid.uuid4()
    v1_id = uuid.uuid4()
    
    historical_version = DataProductVersion(
        id=v1_id,
        data_product_id=prod_id,
        version_number="1.0.0",
        commit_message="Baseline calibrated",
        filepath="/static/historical/ortho_v1.tif",
        original_filename="ortho_v1.tif",
        file_size=80000000,
        bbox=[-86.9, 40.4, -86.8, 40.5],
        crs={"epsg": 4326},
        resolution={"x": 0.03, "y": 0.03},
        is_current=False,
    )

    target_product = MockDataProduct(id=prod_id)
    target_product.filepath = "/static/active/ortho_v2.tif"

    mock_session = MagicMock()
    mock_db.__enter__.return_value = mock_session
    mock_session.get.side_effect = lambda model, obj_id: historical_version if obj_id == v1_id else target_product

    result = crud_version.checkout_version(mock_db, data_product_id=prod_id, version_id=v1_id)

    assert result is not None
    assert result.is_current is True
    assert target_product.filepath == "/static/historical/ortho_v1.tif"
    assert target_product.file_size == 80000000
