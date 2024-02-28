import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio

from app.utils.toolbox.exg import run


multispectral_dataset = Path("/app/app/tests/data/test_multispectral.tif")
validation_dataset = Path("/app/app/tests/data/exg_validation.tif")


def compare_results(tool_results: str):
    """Performs element-wise comparision between test dataset and validation dataset.

    Args:
        tool_results (str): Path to tool output (test) dataset.
    """
    with rasterio.open(validation_dataset) as validation_src:
        with rasterio.open(tool_results) as test_src:
            validation_band_count = validation_src.count
            test_band_count = test_src.count
            assert validation_band_count == test_band_count

            validation_array = validation_src.read(1)
            test_array = test_src.read(1)

            assert np.isclose(validation_array, test_array, atol=0.00001).all()


def test_results_from_exg_tool():
    """Test results from exg script against validation dataset."""
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        in_raster = Path(tmpdir / multispectral_dataset.name)
        out_raster = Path(tmpdir / "exg.tif")
        params = {"red_band_idx": 3, "green_band_idx": 2, "blue_band_idx": 1}

        shutil.copyfile(multispectral_dataset, in_raster)

        run(in_raster, out_raster, params)

        compare_results(out_raster)
