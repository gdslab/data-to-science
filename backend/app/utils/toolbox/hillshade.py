import argparse
import os
import subprocess

import rasterio


def run(in_raster: str, out_raster: str, params: dict = {}) -> str:
    """Create hillshade raster from input raster.

    Args:
        in_raster (str): Filepath for input raster.
        out_raster (str): Filepath for output raster.
        params (dict): Parameters for hillshade tool. No parameters are required.

    Raises:
        ValueError: Input raster must be a single band raster.
        ValueError: Input raster must have a CRS.
        RuntimeError: Failed to create hillshade raster.

    Returns:
        str: Filepath for output raster.
    """
    # Confirm this is a single band raster
    with rasterio.open(in_raster) as src:
        if src.count != 1:
            raise ValueError("Input raster must be a single band raster")
        if src.crs is None:
            raise ValueError("Input raster must have a CRS")

        is_geographic = src.crs.is_geographic

    z_factor = 111120 if is_geographic else 1

    try:
        # Create hillshade raster with gdaldem
        subprocess.run(
            [
                "gdaldem",
                "hillshade",
                in_raster,
                out_raster,
                "-z",
                str(z_factor),
                "-compute_edges",
                "-multidirectional",
                "-of",
                "GTIFF",
            ],
            check=True,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to create hillshade raster: {e.stderr.decode('utf-8')}"
        ) from e

    return out_raster


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create hillshade raster from input raster."
    )
    parser.add_argument(
        "--in_raster",
        type=str,
        required=True,
        help="Filepath for input raster",
    )
    parser.add_argument(
        "--out_raster",
        type=str,
        required=True,
        help="Filepath for output raster",
    )

    args = parser.parse_args()

    if not os.path.exists(args.in_raster):
        raise FileNotFoundError(f"Input raster not found")

    if os.path.exists(args.out_raster):
        raise FileExistsError(f"Output raster already exists")

    run(args.in_raster, args.out_raster)
