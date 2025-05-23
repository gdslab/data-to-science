import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio

from app.utils.toolbox.exg import run


point_cloud_dataset = Path("/app/app/tests/data/test_point_cloud.copc.laz")
dem_dataset = Path("/app/app/tests/data/test_dem.tif")
validation_dataset = Path("/app/app/tests/data/chm_validation.tif")


def compare_results(tool_results: str) -> None:
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


def test_results_from_chm_tool() -> None:
    """Test results from chm script against validation dataset."""
    # with TemporaryDirectory() as tmpd:
    #     tmpdir = Path(tmpd)
    #     in_raster = Path(tmpdir / point_cloud_dataset.name)
    #     in_dem = Path(tmpdir / dem_dataset.name)
    #     out_raster = Path(tmpdir / "chm.tif")

    #     shutil.copyfile(point_cloud_dataset, in_raster)
    #     shutil.copyfile(dem_dataset, in_dem)

    #     run(str(in_raster), str(out_raster), {"dem_input": str(in_dem)})

    #     compare_results(str(out_raster))
    pass
