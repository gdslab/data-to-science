import argparse
import os

import numpy as np
import rasterio


def run(in_raster: str, out_raster: str, params: dict) -> str:
    """Main function for creating VARI raster from input raster. Output
    VARI raster will be stored as a GeoTIFF in the 'out_dir' location.

    Args:
        in_raster (str): Filepath for input raster.
        out_raster (str): Filepath for output raster.
        params (dict): Red, green, and blue band indexes.

    Returns:
        out_raster (str): Filepath for output raster.
    """
    validate_params(params)

    with rasterio.open(in_raster) as src:
        assert src.count >= 3  # assert at least 3 bands available
        assert len(set(src.dtypes)) == 1  # assert each band has same dtype
        dtype = src.dtypes[0]  # dtype from first band

        # update source raster profile to single band and float32
        profile = src.profile
        profile.update(
            dtype=rasterio.float32, count=1, compress="deflate", BIGTIFF="YES"
        )

        # use block windows to calculate vari and write to new file
        with rasterio.open(out_raster, "w", **profile) as dst:
            # all bands must have same block window shapes
            assert len(set(src.block_shapes)) == 1

            # indexes for bands in img array
            red_band_img_idx = 0
            green_band_img_idx = 1
            blue_band_img_idx = 2

            # iterate over each block window
            for ji, window in src.block_windows(1):
                # initialize array to store band values
                img = np.zeros((3, window.height, window.width), dtype=dtype)

                # red band
                img[red_band_img_idx, :, :] = src.read(
                    params.get("red_band_idx"), window=window
                )
                # green band
                img[green_band_img_idx, :, :] = src.read(
                    params.get("green_band_idx"), window=window
                )
                # blue band
                img[blue_band_img_idx, :, :] = src.read(
                    params.get("blue_band_idx"), window=window
                )

                # calculate vari for current window
                red = img[red_band_img_idx, :, :].astype(np.float32)
                green = img[green_band_img_idx, :, :].astype(np.float32)
                blue = img[blue_band_img_idx, :, :].astype(np.float32)

                vari = (green - red) / (green + red - blue)

                # write vari window to out raster
                dst.write(vari, window=window, indexes=1)

    return out_raster


def validate_params(params: dict) -> None:
    """Validate parameters for VARI tool.
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
        description="Creates a vegetation index data product."
    )
    parser.add_argument("in_raster", type=str, help="Path to RGB raster file")
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
