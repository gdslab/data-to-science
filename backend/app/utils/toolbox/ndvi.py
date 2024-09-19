import argparse
import os

import numpy as np
import rasterio


def run(in_raster: str, out_raster: str, params: dict) -> str:
    """Main function for creating NDVI raster from input raster. Output
    NDVI raster will be stored as a GeoTIFF in the 'out_dir' location.

    Args:
        in_raster (str): Filepath for input raster.
        out_raster (str): Filepath for output raster.
        params (dict): Red band and NIR band indexes.

    Returns:
        out_raster (str): Filepath for output raster.
    """
    validate_params(params)

    # input file name
    in_fn = in_raster

    with rasterio.open(in_raster) as src:
        assert src.count >= 2  # assert at least 2 bands available
        assert len(set(src.dtypes)) == 1  # assert each band has same dtype
        dtype = src.dtypes[0]  # dtype from first band

        # update source raster profile to single band and float32
        profile = src.profile
        profile.update(
            dtype=rasterio.float32, count=1, compress="deflate", BIGTIFF="YES"
        )

        # use block windows to calculate exg and write to new file
        with rasterio.open(out_raster, "w", **profile) as dst:
            # all bands must have same block window shapes
            assert len(set(src.block_shapes)) == 1

            # indexes for bands in img array
            red_band_img_idx = 0
            nir_band_img_idx = 1

            # iterate over each block window
            for ji, window in src.block_windows(1):
                # initialize array to store band values
                img = np.zeros((2, window.height, window.width), dtype=dtype)

                # read bands into initialized array
                for i in range(2):
                    # red band
                    img[red_band_img_idx, :, :] = src.read(
                        params.get("red_band_idx"), window=window
                    )
                    # nir band
                    img[nir_band_img_idx, :, :] = src.read(
                        params.get("nir_band_idx"), window=window
                    )

                # calculate ndvi
                nir = img[nir_band_img_idx, :, :].astype(np.float32)
                red = img[red_band_img_idx, :, :].astype(np.float32)
                ndvi = (nir - red) / (nir + red)

                # write ndvi window to out raster
                dst.write(ndvi, window=window, indexes=1)

    return out_raster


def validate_params(params: dict) -> None:
    """Validate parameters for NDVI tool.
    Checks for missing parameters and incorrect data types.

    Args:
        params (dict): Input parameters.

    Raises:
        ValueError: Raise if red band index is missing.
        TypeError: Raise if red band index is not integer.
        ValueError: Raise if nir band index is missing.
        TypeError: Raise if nir band index is not integer.
    """
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

    if not os.path.exists(args.in_raster):
        raise FileNotFoundError("Input raster not found")

    params = {
        "red_band_idx": args.red,
        "nir_band_idx": args.nir,
    }

    run(args.in_raster, args.out_raster, params)
