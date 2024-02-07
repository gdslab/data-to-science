import argparse
import os

import numpy as np
from osgeo import gdal, gdalnumeric, ogr, osr

from app.utils.toolbox.lib import rs3

GDAL_DRIVER = "ENVI"


def run(in_raster: str, out_raster: str, params: dict) -> None:
    """Main function for creating NDVI raster from input raster. Output
    NDVI raster will be stored as a GeoTIFF in the 'out_dir' location.

    Args:
        in_raster (str): Filepath for input raster
        out_raster (str): Filepath for output raster
        params (dict): Red band and NIR band indexes

    Returns:
        out_raster (str): Filepath for output raster
    """
    validate_params(params)

    # Input file name
    in_fn = in_raster

    # Open image without loading to memory
    in_img = rs3.RSImage(in_fn)

    # Initialize output array
    out_arr = np.zeros((1, in_img.ncol, in_img.nrow), dtype=np.float32)

    # Read bands
    nir = in_img.img[params.get("nir_band_idx"), :, :].astype(np.float32)
    red = in_img.img[params.get("red_band_idx"), :, :].astype(np.float32)

    # Calculate normalized difference vegetation index
    b1 = nir - red
    b2 = nir + red
    ndvi = b1 / b2

    # Save image
    driver = gdal.GetDriverByName(GDAL_DRIVER)
    outds = driver.Create(
        out_raster,
        in_img.ds.RasterXSize,
        in_img.ds.RasterYSize,
        1,
        gdal.GDT_Float32,
    )
    outds.SetGeoTransform(in_img.ds.GetGeoTransform())
    outds.SetProjection(in_img.ds.GetProjection())
    outds.GetRasterBand(1).WriteArray(ndvi)
    outds = None

    return out_raster


def validate_params(params: dict) -> None:
    if "red_band_idx" not in params:
        raise ValueError("Red band index param (red_band_idx) missing")
    if type(params.get("red_band_idx")) != int:
        raise TypeError("Red band index must be an integer")
    if "nir_band_idx" not in params:
        raise ValueError("NIR band index param (nir_band_idx) missing")
    if type(params.get("nir_band_idx")) != int:
        raise TypeError("NIR band index must be an integer")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Creates a normalized difference vegetation index data product."
    )
    parser.add_argument("in_raster", type=str, help="Path to multispectral raster file")
    parser.add_argument("out_raster", type=str, help="Full path for output raster")
    parser.add_argument("--red", type=int, help="Red band index")
    parser.add_argument("--nir", type=int, help="Near-infrared band index")

    args = parser.parse_args()
    params = {
        "red_band_idx": args.red,
        "nir_band_idx": args.nir,
    }

    run(args.in_raster, args.out_raster, params)
