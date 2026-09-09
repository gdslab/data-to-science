import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest
import rasterio

from app.tests.utils.utils import write_gray_alpha_raster, write_raster_without_stats
from app.utils.toolbox.hillshade import run

dsm_dataset = Path("/app/app/tests/data/test.tif")
hillshade_validation = Path("/app/app/tests/data/hillshade_validation.tif")


def compare_results(tool_results: str) -> None:
    """Performs element-wise comparision between test dataset and validation dataset.

    Args:
        tool_results (str): Path to tool output (test) dataset.
    """
    with rasterio.open(str(hillshade_validation)) as validation_src:
        with rasterio.open(tool_results) as test_src:
            validation_band_count = validation_src.count
            test_band_count = test_src.count
            assert validation_band_count == test_band_count

            validation_array = validation_src.read(1)
            test_array = test_src.read(1)

            assert np.isclose(validation_array, test_array, atol=0.00001).all()


def test_results_from_hillshade_tool() -> None:
    """Test results from hillshade script against validation dataset."""
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        in_raster = tmpdir_path / dsm_dataset.name
        out_raster = tmpdir_path / "hillshade.tif"

        shutil.copyfile(str(dsm_dataset), str(in_raster))

        run(str(in_raster), str(out_raster))

        compare_results(str(out_raster))


def test_hillshade_tool_accepts_a_data_band_with_an_alpha_band() -> None:
    """A raster with an alpha band hillshades the same as its band 1 alone."""
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        two_band = write_gray_alpha_raster(tmpdir_path / "dsm_alpha.tif")

        with rasterio.open(two_band) as src:
            profile = {**src.profile, "count": 1}
            profile.pop("alpha", None)
            data = src.read(1)
        one_band = tmpdir_path / "dsm.tif"
        with rasterio.open(one_band, "w", **profile) as dst:
            dst.write(data, 1)

        run(str(two_band), str(tmpdir_path / "hillshade_alpha.tif"))
        run(str(one_band), str(tmpdir_path / "hillshade.tif"))

        with rasterio.open(tmpdir_path / "hillshade_alpha.tif") as from_two_band:
            with rasterio.open(tmpdir_path / "hillshade.tif") as from_one_band:
                assert from_two_band.count == 1
                assert np.array_equal(from_two_band.read(1), from_one_band.read(1))


def test_hillshade_tool_rejects_a_multiband_raster() -> None:
    with TemporaryDirectory() as tmpdir:
        in_raster = write_raster_without_stats(Path(tmpdir) / "rgb.tif", count=3)

        with pytest.raises(ValueError, match="single band"):
            run(str(in_raster), str(Path(tmpdir) / "hillshade.tif"))
