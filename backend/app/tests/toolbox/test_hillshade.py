import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio

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
