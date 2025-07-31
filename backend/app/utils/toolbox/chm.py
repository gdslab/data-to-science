import argparse
import json
import os
import shutil
import subprocess
import tempfile

import laspy as lp
import numpy as np
import rasterio
from osgeo import gdal, osr
from rasterio.fill import fillnodata


def run(in_point_cloud: str, out_raster: str, params: dict) -> str:
    """Main function for creating CHM raster from input point cloud.
    Output CHM raster will be stored as a GeoTIFF in the 'out_dir' location.

    Args:
        in_point_cloud (str): Filepath for input point cloud.
        out_raster (str): Filepath for output raster.
        params (dict): DEM data product filepath, resolution, and percentile.

    Returns:
        out_raster (str): Filepath for output raster.
    """
    validate_params(params)

    input_dem_raster = params["dem_input"]
    spatial_resolution = float(params["chm_resolution"])
    percentile = float(params["chm_percentile"])

    # Create temporary directory in the same folder as input point cloud
    input_dir = os.path.dirname(os.path.abspath(in_point_cloud))
    temp_dir = os.path.join(input_dir, "tmp_chm_processing")
    os.makedirs(temp_dir, exist_ok=True)

    temp_normalized_las = os.path.join(temp_dir, "normalized_points.las")

    try:
        # construct pdal pipeline for generating chm
        chm_pipeline = [
            in_point_cloud,
            {
                "type": "filters.hag_dem",
                "raster": input_dem_raster,
            },
            {
                "type": "writers.las",
                "filename": temp_normalized_las,
                "extra_dims": "HeightAboveGround=float32",
            },
        ]

        # execute pdal pipeline
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(chm_pipeline, tmp)
            tmp.flush()
            subprocess.run(["pdal", "pipeline", tmp.name], check=True)

        las = lp.read(temp_normalized_las)

        boundary_ul = [las.header.mins[0], las.header.maxs[1]]
        boundary_br = [las.header.maxs[0], las.header.mins[1]]
        raster_x_size = int(abs(boundary_br[0] - boundary_ul[0]) / spatial_resolution)
        raster_y_size = int(abs(boundary_br[1] - boundary_ul[1]) / spatial_resolution)
        transform_out = (
            boundary_ul[0],
            spatial_resolution,
            0,
            boundary_ul[1],
            0,
            -spatial_resolution,
        )

        crs = las.header.parse_crs()
        srs_out = osr.SpatialReference()
        try:
            srs_out.ImportFromEPSG(int(crs.to_epsg()))
        except TypeError:
            srs_out.ImportFromWkt(crs.to_wkt())
        except Exception as e:
            raise ValueError(f"Error importing CRS: {e}")

        x = np.array(las.x)
        y = np.array(las.y)
        z = las["HeightAboveGround"]
        del las

        img_x_chm = np.round((x - boundary_ul[0]) / spatial_resolution)
        img_y_chm = np.round((boundary_ul[1] - y) / spatial_resolution)
        del x, y

        # region - Aggregating points by image coordinates - chm

        dict_pts_chm: dict[tuple[int, int], list[float]] = {}
        n_p = int(0)
        num_pts = len(z)
        while n_p < num_pts:
            tmp_key = (int(img_x_chm[n_p]), int(img_y_chm[n_p]))
            if not tmp_key in dict_pts_chm.keys():
                dict_pts_chm[tmp_key] = [z[n_p]]
            else:
                dict_pts_chm[tmp_key].append(z[n_p])
            del tmp_key

            n_p += 1
        del n_p, num_pts

        # endregion

        # region - Generate chm
        nop = np.zeros((raster_y_size, raster_x_size), dtype=np.float32)
        chm = np.zeros((raster_y_size, raster_x_size), dtype=np.float32) - 9999
        for n_x in range(raster_x_size):
            for n_y in range(raster_y_size):
                if (n_x, n_y) in dict_pts_chm.keys():
                    chm[n_y, n_x] = np.percentile(
                        dict_pts_chm[(n_x, n_y)], float(percentile)
                    )
                    nop[n_y, n_x] = len(dict_pts_chm[(n_x, n_y)])
        del n_x, n_y

        out_format = "GTiff"
        driver = gdal.GetDriverByName(out_format)

        chm_ds = driver.Create(
            out_raster, chm.shape[1], chm.shape[0], 1, gdal.GDT_Float32
        )
        chm_ds.SetGeoTransform(transform_out)
        chm_ds.SetProjection(srs_out.ExportToWkt())
        chm_ds.GetRasterBand(1).WriteArray(chm)
        chm_ds.GetRasterBand(1).SetNoDataValue(-9999)
        chm_ds = None
        del out_format, driver

        with rasterio.open(out_raster, "r+") as src:
            n_band = 1
            arr = src.read(1)

            mask = arr != -9999
            arr_filled = fillnodata(
                arr,
                mask=mask,
                max_search_distance=spatial_resolution * 5,
                smoothing_iterations=0,
            )

            src.write_band(n_band, arr_filled)
        del src, arr, arr_filled, n_band

    finally:
        # Clean up temporary directory and all its contents
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

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

    if "chm_resolution" not in params:
        raise ValueError("CHM resolution is required")

    if "chm_percentile" not in params:
        raise ValueError("CHM percentile is required")

    # Check if values are numbers before checking ranges
    if not isinstance(params["chm_resolution"], (int, float)):
        raise ValueError("CHM resolution must be a number")

    if not isinstance(params["chm_percentile"], (int, float)):
        raise ValueError("CHM percentile must be a number")

    if params["chm_resolution"] <= 0:
        raise ValueError("CHM resolution must be greater than 0")

    if params["chm_percentile"] < 0 or params["chm_percentile"] > 100:
        raise ValueError("CHM percentile must be between 0 and 100")


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
    parser.add_argument(
        "--chm_resolution",
        type=float,
        required=True,
        default=0.5,
        help="CHM resolution",
    )
    parser.add_argument(
        "--chm_percentile",
        type=float,
        required=True,
        default=98.0,
        help="CHM percentile",
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
        "chm_resolution": args.chm_resolution,
        "chm_percentile": args.chm_percentile,
    }

    run(args.in_point_cloud, args.out_raster, params)
