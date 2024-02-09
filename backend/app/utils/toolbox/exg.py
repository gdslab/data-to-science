import argparse
import os

import numpy as np
from osgeo import gdal

from app.utils.toolbox.lib import rs3

gdal.UseExceptions()

GDAL_DRIVER = "ENVI"


def run(in_raster: str, out_raster: str, params: dict) -> None:
    """Main function for creating Excess Green Index raster from input raster.
    Output EXG raster will be stored as a GeoTIFF in the 'out_dir' location.

    Args:
        in_raster (str): Filepath for input raster.
        out_raster (str): Filepath for output raster.
        params (dict): Red, green, and blue band indexes.

    Returns:
        out_raster (str): Filepath for output raster.
    """
    validate_params(params)

    # Input file name
    in_fn = in_raster

    # Open image without loading to memory
    in_img = rs3.RSImage(in_fn)

    # Read bands
    red = in_img.img[params.get("red_band_idx"), :, :].astype(np.float32)
    green = in_img.img[params.get("green_band_idx"), :, :].astype(np.float32)
    blue = in_img.img[params.get("blue_band_idx"), :, :].astype(np.float32)

    # Calculate excess green vegetation index
    red_s = red / (red + green + blue)
    green_s = green / (red + green + blue)
    blue_s = blue / (red + green + blue)

    exg = 2 * green_s - red_s - blue_s

    # Save image
    driver = gdal.GetDriverByName(GDAL_DRIVER)
    outds = driver.Create(
        out_raster, in_img.ds.RasterXSize, in_img.ds.RasterYSize, 1, gdal.GDT_Float32
    )
    outds.SetGeoTransform(in_img.ds.GetGeoTransform())
    outds.SetProjection(in_img.ds.GetProjection())
    outds.GetRasterBand(1).WriteArray(exg)
    outds = None

    return out_raster


def validate_params(params: dict) -> None:
    """Validate parameters for EXG tool.
    Checks for missing parameters and incorrect data types.

    Args:
        params (dict): Input parameters.

    Raises:
        ValueError: Raise if red band index is missing.
        TypeError: Raise if red band index is not integer.
        ValueError: Raise if green band index is missing.
        TypeError: Raise if green band index is not integer.
        ValueError: Raise if blue band index is missing.
        TypeError: Raise if blue band index is not integer.
    """
    if "red_band_idx" not in params:
        raise ValueError("Red band index param (red_band_idx) missing")
    if type(params.get("red_band_idx")) != int:
        raise TypeError("Red band index must be an integer")
    if "green_band_idx" not in params:
        raise ValueError("Green band index param (green_band_idx) missing")
    if type(params.get("green_band_idx")) != int:
        raise TypeError("Green band index must be an integer")
    if "blue_band_idx" not in params:
        raise ValueError("Blue band index param (blue_band_idx) missing")
    if type(params.get("blue_band_idx")) != int:
        raise TypeError("Blue band index must be an integer")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Creates a excess green index index data product."
    )
    parser.add_argument("in_raster", type=str, help="Path to multispectral raster file")
    parser.add_argument("out_raster", type=str, help="Full path for output raster")
    parser.add_argument("--red", type=int, help="Red band index")
    parser.add_argument("--green", type=int, help="Green band index")
    parser.add_argument("--blue", type=int, help="Blue band index")

    args = parser.parse_args()

    if not os.path.exists(args.in_raster):
        raise FileNotFoundError("Input raster not found")

    if os.path.exists(args.out_raster):
        raise FileExistsError("Output raster already exists")

    params = {
        "red_band_idx": args.red,
        "green_band_idx": args.green,
        "blue_band_idx": args.blue,
    }

    run(args.in_raster, args.out_raster, params)
