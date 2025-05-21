import argparse
import json
import os
import subprocess
import tempfile


def run(in_point_cloud: str, out_raster: str, params: dict) -> str:
    """Main function for creating CHM raster from input point cloud.
    Output CHM raster will be stored as a GeoTIFF in the 'out_dir' location.

    Args:
        in_point_cloud (str): Filepath for input point cloud.
        out_raster (str): Filepath for output raster.
        params (dict): DEM data product filepath.

    Returns:
        out_raster (str): Filepath for output raster.
    """
    validate_params(params)

    temp_las = None

    # check if point cloud is COPC
    if in_point_cloud.endswith(".copc.laz"):
        # create temp las file
        temp_las = tempfile.NamedTemporaryFile(suffix=".las", delete=False).name

        # copc to las pipeline
        copc_to_las_pipeline = [
            {"type": "readers.copc", "filename": in_point_cloud},
            {"type": "writers.las", "filename": temp_las},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(copc_to_las_pipeline, tmp)
            tmp.flush()
            subprocess.run(["pdal", "pipeline", tmp.name], check=True)

        las_input = temp_las
    else:
        las_input = in_point_cloud

    input_dem_raster = params["dem_input"]

    # construct pdal pipeline for generating chm
    chm_pipeline = [
        {
            "type": "readers.las",
            "filename": las_input,
        },
        {
            "type": "filters.hag_dem",
            "raster": input_dem_raster,
        },
        {"type": "filters.ferry", "dimensions": "HeightAboveGround=>Z"},
        {
            "type": "writers.gdal",
            "filename": out_raster,
            "resolution": 0.1,
            "output_type": "max",
            "data_type": "float",
        },
    ]

    # execute pdal pipeline
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(chm_pipeline, tmp)
        tmp.flush()
        subprocess.run(["pdal", "pipeline", tmp.name], check=True)

    # remove the temp las input
    if temp_las and os.path.exists(temp_las):
        os.remove(temp_las)

    return out_raster


def validate_params(params: dict) -> None:
    """Validate parameters for CHM tool.

    Args:
        params (dict): Parameters for CHM tool.
    """
    if "dem_input" not in params:
        raise ValueError("DEM data product filepath is required")

    if not os.path.exists(params["dem_input"]):
        raise FileNotFoundError(
            f"DEM data product filepath does not exist: {params['dem_input']}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create CHM raster from input point cloud."
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
        "--dem_input", type=str, required=True, help="DEM data product filepath"
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
        "dem_input": args.dem_input,
    }

    run(args.in_point_cloud, args.out_raster, params)
