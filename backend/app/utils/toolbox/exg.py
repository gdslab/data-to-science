import argparse
import os

import numpy as np
import rasterio


def run(in_raster: str, out_raster: str, params: dict) -> str:
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

    # input file name
    in_fn = in_raster

    with rasterio.open(in_raster) as src:
        nband = src.count  # number of bands
        assert len(set(src.dtypes)) == 1  # assert each band has same dtype
        dtype = src.dtypes[0]  # dtype from first band

        # update source raster profile to single band and float32
        profile = src.profile
        profile.update(dtype=rasterio.float32, count=1, compress="deflate")

        # use block windows to calculate exg and write to new file
        with rasterio.open(out_raster, "w", **profile) as dst:
            # all bands must have same block window shapes
            assert len(set(src.block_shapes)) == 1

            # iterate over each block window
            for ji, window in src.block_windows(1):
                # initialize array to store band values
                img = np.zeros((nband, window.height, window.width), dtype=dtype)

                # read bands into initialized array
                for i in range(nband):
                    band = src.read(i + 1, window=window)
                    img[i, :, :] = band

                # calculate exg for current window
                red = img[params.get("red_band_idx"), :, :].astype(np.float32)
                green = img[params.get("green_band_idx"), :, :].astype(np.float32)
                blue = img[params.get("blue_band_idx"), :, :].astype(np.float32)

                red_s = red / (red + green + blue)
                green_s = green / (red + green + blue)
                blue_s = blue / (red + green + blue)

                exg = 2 * green_s - red_s - blue_s

                # write exg window to out raster
                dst.write(exg, window=window, indexes=1)

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
