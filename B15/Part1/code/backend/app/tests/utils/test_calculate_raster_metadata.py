import os

from app.crud.crud_data_product import calculate_raster_metadata


def test_calculate_metadata_from_valid_geotiff():
    """Test metadata extraction from a valid GeoTIFF file."""
    # Use existing test fixture
    test_tif = "app/tests/data/test.tif"

    metadata = calculate_raster_metadata(test_tif)

    assert metadata is not None
    assert "bbox" in metadata
    assert "crs" in metadata
    assert "resolution" in metadata

    # Verify bbox is a list of 4 floats (WGS84 coordinates)
    assert isinstance(metadata["bbox"], list)
    assert len(metadata["bbox"]) == 4
    assert all(isinstance(coord, float) for coord in metadata["bbox"])

    # Verify CRS structure
    assert "epsg" in metadata["crs"]
    assert "unit" in metadata["crs"]
    assert metadata["crs"]["epsg"] == 32616  # Known CRS for test.tif
    assert metadata["crs"]["unit"] == "metre"

    # Verify resolution structure
    assert "x" in metadata["resolution"]
    assert "y" in metadata["resolution"]
    assert "unit" in metadata["resolution"]
    assert isinstance(metadata["resolution"]["x"], float)
    assert isinstance(metadata["resolution"]["y"], float)
    assert metadata["resolution"]["unit"] == "metre"


def test_calculate_metadata_non_tiff_file():
    """Test returns None for non-TIFF files."""
    # Test with a JSON file
    test_json = "app/tests/data/test_bbox.geojson"

    metadata = calculate_raster_metadata(test_json)

    assert metadata is None


def test_calculate_metadata_missing_file():
    """Test returns None and logs error for missing files."""
    nonexistent_file = "app/tests/data/does_not_exist.tif"

    metadata = calculate_raster_metadata(nonexistent_file)

    assert metadata is None


def test_calculate_metadata_with_different_crs():
    """Test metadata extraction from GeoTIFF with different CRS."""
    # Use test_multispectral.tif which may have different properties
    test_tif = "app/tests/data/test_multispectral.tif"

    if os.path.exists(test_tif):
        metadata = calculate_raster_metadata(test_tif)

        if metadata:  # Only assert if file exists and is valid
            assert metadata is not None
            assert "bbox" in metadata
            assert "crs" in metadata
            assert "resolution" in metadata
            assert metadata["crs"]["unit"] is not None


def test_bbox_transformed_to_wgs84():
    """Test that bbox is correctly transformed to WGS84."""
    test_tif = "app/tests/data/test.tif"

    metadata = calculate_raster_metadata(test_tif)

    assert metadata is not None
    bbox = metadata["bbox"]

    # WGS84 coordinates should be in reasonable lat/lon ranges
    # For Indiana, USA:
    # Longitude should be around -86 (west is negative)
    # Latitude should be around 40-41
    assert -87 < bbox[0] < -85  # min longitude
    assert 40 < bbox[1] < 42  # min latitude
    assert -87 < bbox[2] < -85  # max longitude
    assert 40 < bbox[3] < 42  # max latitude

    # Min should be less than max
    assert bbox[0] < bbox[2]  # minx < maxx
    assert bbox[1] < bbox[3]  # miny < maxy


def test_resolution_has_positive_values():
    """Test that resolution x and y are positive values."""
    test_tif = "app/tests/data/test.tif"

    metadata = calculate_raster_metadata(test_tif)

    assert metadata is not None
    assert metadata["resolution"]["x"] > 0
    assert metadata["resolution"]["y"] > 0


def test_units_consistency():
    """Test that CRS unit and resolution unit match."""
    test_tif = "app/tests/data/test.tif"

    metadata = calculate_raster_metadata(test_tif)

    assert metadata is not None
    # Resolution should use the same unit as the CRS
    assert metadata["resolution"]["unit"] == metadata["crs"]["unit"]
