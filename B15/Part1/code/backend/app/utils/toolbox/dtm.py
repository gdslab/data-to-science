import argparse
import json
import os
import subprocess
import tempfile

import rasterio
from rasterio.fill import fillnodata


def run(in_point_cloud: str, out_raster: str, params: dict) -> str:
    validate_params(params)

    spatial_resolution = float(params["dtm_resolution"])
    rigidness = int(params["dtm_rigidness"])

    dtm_pipeline = [
        in_point_cloud,
        {"type": "filters.assign", "assignment": "Classification[:]=0"},
        {
            "type": "filters.csf",
            "resolution": spatial_resolution * 2,
            "rigidness": rigidness,
            "smooth": True,
        },
        {"type": "filters.range", "limits": "Classification[2:2]"},
        {
            "filename": out_raster,
            "gdaldriver": "GTiff",
            "output_type": "min",
            "resolution": spatial_resolution,
            "type": "writers.gdal",
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(dtm_pipeline, tmp)
        tmp.flush()
        subprocess.run(["pdal", "pipeline", tmp.name], check=True)

    with rasterio.open(out_raster, "r+") as src:
        arr = src.read(1)
        mask = arr != -9999
        arr_filled = fillnodata(arr, mask=mask, smoothing_iterations=0)
        src.write_band(1, arr_filled)

    del src, arr, arr_filled, mask

    return out_raster


def validate_params(params: dict) -> None:
    if "dtm_resolution" not in params:
        raise ValueError("DTM resolution is required")
    if "dtm_rigidness" not in params:
        raise ValueError("DTM rigidness is required")

    # Check if values are numbers before checking ranges
    if not isinstance(params["dtm_resolution"], (int, float)):
        raise ValueError("DTM resolution must be a number")
    if not isinstance(params["dtm_rigidness"], int):
        raise ValueError("DTM rigidness must be an integer")

    if params["dtm_resolution"] <= 0:
        raise ValueError("DTM resolution must be greater than 0")

    if params["dtm_rigidness"] < 1 or params["dtm_rigidness"] > 3:
        raise ValueError("DTM rigidness must be between 1 and 3")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create DTM raster from input point cloud."
    )
    parser.add_argument(
        "--in_point_cloud",
        type=str,
        required=True,
        help="Filepath for input point cloud",
    )
    parser.add_argument(
        "--out_raster", type=str, required=True, help="Filepath for output raster"
    )
    parser.add_argument(
        "--dtm_resolution",
        type=float,
        required=True,
        default=0.5,
        help="DTM resolution",
    )
    parser.add_argument(
        "--dtm_rigidness", type=int, required=True, default=2, help="DTM rigidness"
    )
    args = parser.parse_args()

    if not os.path.exists(args.in_point_cloud):
        raise FileNotFoundError(
            f"Input point cloud filepath does not exist: {args.in_point_cloud}"
        )

    if os.path.exists(args.out_raster):
        raise FileExistsError(
            f"Output raster filepath already exists: {args.out_raster}"
        )

    params = {
        "dtm_resolution": args.dtm_resolution,
        "dtm_rigidness": args.dtm_rigidness,
    }

    run(args.in_point_cloud, args.out_raster, params)
