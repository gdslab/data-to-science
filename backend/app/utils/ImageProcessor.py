import json
import logging
import multiprocessing
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, List, NoReturn, Optional

import rasterio
from pydantic import ValidationError

from app.schemas.user_style import UserStyleCreate
from app.utils.stac.STACProperties import (
    ImageStructure,
    Metadata,
    STACProperties,
    STACPropertiesValidator,
    Stats,
)

logger = logging.getLogger(__name__)

# Interpolating methods smooth categorical rasters, but those are rare enough
# that a consistent choice for continuous data is the better trade-off.
MULTIBAND_RESAMPLING = "cubic"
DEFAULT_RESAMPLING = "bilinear"


class ImageProcessor:
    """
    Used to process uploaded rasters in the GeoTIFF format. If the raster is not
    using the Cloud Optimized GeoTIFF (COG) layout, one will be generated. A small
    preview image is created alongside it.
    """

    def __init__(
        self,
        in_raster: str,
        output_dir: str | Path | None = None,
        project_to_utm: bool = False,
    ) -> None:
        self.in_raster = Path(in_raster)

        if not output_dir:
            output_dir = self.in_raster.parents[1]

        self.out_dir = Path(output_dir)
        self.out_raster = self.out_dir / self.in_raster.name
        self.preview_out_path = self.out_raster.with_suffix(".jpg")
        self.project_to_utm = project_to_utm
        self.resampling = DEFAULT_RESAMPLING

        self.stac_properties: STACProperties = {"raster": [], "eo": []}

    def run(self) -> Path:
        logger.debug("Getting raster info from gdalinfo")
        info: dict = get_info(self.in_raster, with_stats=False)
        self.resampling = resampling_for(len(info.get("bands", [])))

        logger.debug("Checking if raster is in COG layout")
        epsg_code: str | None = self.get_utm_epsg() if self.project_to_utm else None

        # A COG still has to be rewritten when it needs reprojecting.
        if is_cog(info) and not epsg_code:
            logger.info("Raster is in COG layout, moving to output directory")
            shutil.move(self.in_raster, self.out_dir)
        else:
            logger.info("Converting raster to COG layout")
            convert_to_cog(self.in_raster, self.out_raster, self.resampling, epsg_code)

        logger.debug("Cleaning up temporary files")
        if os.path.exists(self.in_raster.parent):
            shutil.rmtree(self.in_raster.parent)

        # Read stats from the output so gdalinfo's sidecar is written next to the
        # COG, not into the input directory removed above.
        info = get_info(self.out_raster)

        logger.debug("Processing STAC properties and creating preview")
        self.stac_properties = get_stac_properties(info)
        create_preview_image(
            self.out_raster,
            self.preview_out_path,
            self.stac_properties,
            self.resampling,
        )

        logger.info(f"Successfully processed raster: {self.out_raster}")
        return self.out_raster

    def get_utm_epsg(self) -> str | None:
        """Returns UTM EPSG code for the input raster, or None if not applicable.

        Returns:
            str | None: EPSG code when the raster is in WGS84, None otherwise.
        """
        wgs84_status, mean_x, mean_y = get_wgs84_info(self.in_raster)
        if wgs84_status and mean_x is not None and mean_y is not None:
            return get_utm_epsg_from_latlon(mean_y, mean_x)

        return None

    def get_default_symbology(self) -> UserStyleCreate | NoReturn:
        """Creates default symbology settings based on raster type and stats."""
        if (
            len(self.stac_properties["raster"]) > 0
            and len(self.stac_properties["eo"]) > 0
        ):
            if len(self.stac_properties["raster"]) == 1:
                stats: Optional[Stats] = self.stac_properties["raster"][0].get("stats")
                if stats is None:
                    raise Exception("Unable to get raster stats")

                return UserStyleCreate(
                    **{
                        "settings": {
                            "colorRamp": "rainbow",
                            "mode": "minMax",
                            "max": stats.get("maximum", 255),
                            "min": stats.get("minimum", 0),
                            "userMax": stats.get("maximum", 255),
                            "userMin": stats.get("minimum", 0),
                            "meanStdDev": 2,
                        }
                    }
                )
            elif len(self.stac_properties["raster"]) > 2:
                symbology: dict = {
                    "mode": "minMax",
                    "meanStdDev": 2,
                    "red": {},
                    "green": {},
                    "blue": {},
                }

                for idx, band in enumerate(["red", "green", "blue"]):
                    stats = self.stac_properties["raster"][idx]["stats"]
                    symbology[band] = {
                        "idx": idx + 1,
                        "min": stats.get("minimum", 0),
                        "max": stats.get("maximum", 255),
                        "userMin": stats.get("minimum", 0),
                        "userMax": stats.get("maximum", 255),
                    }

                return UserStyleCreate(**{"settings": symbology})
            else:
                raise Exception("Need at least three bands for ortho imagery")
        else:
            raise Exception(
                "Cannot get default symbology settings before running processor"
            )


def resampling_for(band_count: int) -> str:
    """Returns the resampling method to use for a raster.

    Args:
        band_count (int): Number of bands in the raster.

    Returns:
        str: GDAL resampling method name.
    """
    return MULTIBAND_RESAMPLING if band_count >= 3 else DEFAULT_RESAMPLING


def run_gdal(command: List[str]) -> subprocess.CompletedProcess:
    """Runs a GDAL command, raising with GDAL's own error message on failure.

    Args:
        command (List[str]): Command and arguments to run.

    Raises:
        subprocess.CalledProcessError: Command returned a non-zero exit code.

    Returns:
        subprocess.CompletedProcess: Completed process with captured output.
    """
    result: subprocess.CompletedProcess = subprocess.run(
        command, capture_output=True, text=True
    )

    if result.returncode != 0:
        logger.error(
            f"{command[0]} exited with {result.returncode}: {result.stderr.strip()}"
        )
        raise subprocess.CalledProcessError(
            result.returncode, command, output=result.stdout, stderr=result.stderr
        )

    return result


def parse_gdalinfo(result: subprocess.CompletedProcess) -> dict:
    """Parses gdalinfo JSON output.

    Args:
        result (subprocess.CompletedProcess): Completed gdalinfo process.

    Raises:
        json.JSONDecodeError: gdalinfo output could not be parsed.

    Returns:
        dict: gdalinfo JSON output.
    """
    try:
        gdalinfo: dict = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        logger.error(str(e))
        raise

    return gdalinfo


def get_info(in_raster: Path, with_stats: bool = True) -> dict | NoReturn:
    """Returns output from gdalinfo -json <input_dataset>.

    Args:
        in_raster (Path): Path to input dataset.
        with_stats (bool): Whether band statistics are required. Defaults to True.

    Raises:
        subprocess.CalledProcessError: gdalinfo returned a non-zero exit code.
        json.JSONDecodeError: gdalinfo output could not be parsed.

    Returns:
        dict: gdalinfo JSON output.
    """
    gdalinfo: dict = parse_gdalinfo(run_gdal(["gdalinfo", "-json", str(in_raster)]))

    if not with_stats:
        return gdalinfo

    # Computing statistics reads the full raster, so skip it when already present.
    if not all(
        "STATISTICS_MINIMUM" in band.get("metadata", {}).get("", {})
        for band in gdalinfo["bands"]
    ):
        gdalinfo = parse_gdalinfo(
            run_gdal(["gdalinfo", "-stats", "-json", str(in_raster)])
        )

    return gdalinfo


def is_cog(info: dict) -> bool:
    """Return True if the input raster is in COG layout.

    Args:
        info (dict): gdalinfo -json output

    Returns:
        bool: True if in COG layout, False otherwise
    """
    if info and info.get("metadata"):
        metadata: Metadata = info["metadata"]
        if isinstance(metadata, dict) and metadata.get("IMAGE_STRUCTURE"):
            image_struct: ImageStructure = metadata["IMAGE_STRUCTURE"]
            if isinstance(image_struct, dict) and image_struct.get("LAYOUT"):
                layout: str = image_struct["LAYOUT"]
                return layout == "COG"
    return False


def get_stac_properties(info: dict) -> STACProperties:
    """Return STAC raster:bands and eo:bands properties from gdalinfo.

    Args:
        info (dict): gdalinfo -stats -hist -json output

    Returns:
        dict: Raster band dtype, stats, histogram, and unit
    """
    stac_properties: STACProperties = {"raster": [], "eo": []}
    if info and info.get("stac"):
        stac: Any | None = info.get("stac")
        if isinstance(stac, dict) and stac.get("raster:bands") and stac.get("eo:bands"):
            try:
                stac_properties = STACPropertiesValidator.validate_python(
                    {"raster": stac.get("raster:bands"), "eo": stac.get("eo:bands")}
                )
            except ValidationError as e:
                logger.error(e)
            except Exception as e:
                logger.error(e)

    return stac_properties


def build_cog_command(
    in_raster: Path,
    out_raster: Path,
    resampling: str = DEFAULT_RESAMPLING,
    epsg_code: str | None = None,
    num_threads: int | None = None,
) -> List[str]:
    """Returns the gdal_translate command used to write a COG.

    Args:
        in_raster (Path): Path to input raster dataset.
        out_raster (Path): Path for output raster dataset.
        resampling (str): Resampling method for warping and overviews.
        epsg_code (str | None): Target EPSG code, or None to keep the source CRS.
        num_threads (int | None, optional): No. of CPUs to use. Defaults to None.

    Returns:
        List[str]: Command and arguments for gdal_translate.
    """
    if not num_threads:
        num_threads = max(1, multiprocessing.cpu_count() // 2)

    command: List[str] = [
        "gdal_translate",
        str(in_raster),
        str(out_raster),
        "-of",
        "COG",
        "-co",
        "COMPRESS=DEFLATE",
        "-co",
        "PREDICTOR=YES",
        "-co",
        f"OVERVIEW_RESAMPLING={resampling}",
        "-co",
        f"NUM_THREADS={num_threads}",
        "-co",
        "BIGTIFF=IF_SAFER",
        "-co",
        "STATISTICS=YES",
    ]

    # The COG driver warps on write; gdal_translate has no reprojection flags.
    if epsg_code:
        command.extend(
            ["-co", f"TARGET_SRS={epsg_code}", "-co", f"WARP_RESAMPLING={resampling}"]
        )

    return command


def convert_to_cog(
    in_raster: Path,
    out_raster: Path,
    resampling: str = DEFAULT_RESAMPLING,
    epsg_code: str | None = None,
    num_threads: int | None = None,
) -> None:
    """Runs gdal_translate to generate new raster in COG layout.

    Args:
        in_raster (Path): Path to input raster dataset.
        out_raster (Path): Path for output raster dataset.
        resampling (str): Resampling method for warping and overviews.
        epsg_code (str | None): Target EPSG code, or None to keep the source CRS.
        num_threads (int | None, optional): No. of CPUs to use. Defaults to None.
    """
    if epsg_code:
        logger.info(f"Projecting raster to {epsg_code}")

    run_gdal(
        build_cog_command(in_raster, out_raster, resampling, epsg_code, num_threads)
    )


def create_preview_image(
    in_raster: Path,
    preview_out_path: Path,
    stac_props: STACProperties,
    resampling: str = DEFAULT_RESAMPLING,
) -> None:
    """Generates preview image for GeoTIFF data products.

    Args:
        in_raster (Path): Path to input dataset.
        preview_out_path (Path): Path for preview image.
        stac_props (STACProperties): gdalinfo STAC output.
        resampling (str): Resampling method used to downsample the preview.
    """
    band_count: int = len(stac_props["raster"])
    if band_count > 2:
        band_params: list = ["-b", "1", "-b", "2", "-b", "3"]
        scale_params: list = [
            "-scale_1",
            str(stac_props["raster"][0]["stats"]["minimum"]),
            str(stac_props["raster"][0]["stats"]["maximum"]),
            "0",
            "255",
            "-scale_2",
            str(stac_props["raster"][1]["stats"]["minimum"]),
            str(stac_props["raster"][1]["stats"]["maximum"]),
            "0",
            "255",
            "-scale_3",
            str(stac_props["raster"][2]["stats"]["minimum"]),
            str(stac_props["raster"][2]["stats"]["maximum"]),
            "0",
            "255",
        ]
    else:
        band_params = ["-b", "1"]
        scale_params = [
            "-scale_1",
            str(stac_props["raster"][0]["stats"]["minimum"]),
            str(stac_props["raster"][0]["stats"]["maximum"]),
            "0",
            "255",
        ]

    outsize_params: list = ["-outsize", "320", "0"]
    inout_params: list = [str(in_raster), str(preview_out_path)]

    command = [
        "gdal_translate",
        "-of",
        "JPEG",
        "-ot",
        "Byte",
        "-co",
        "QUALITY=75",
        "-r",
        resampling,
    ]
    command.extend(band_params)
    command.extend(outsize_params)
    command.extend(scale_params)
    command.extend(inout_params)

    run_gdal(command)


def get_utm_epsg_from_latlon(lat: float, lon: float) -> str:
    """
    Returns an EPSG code string for the UTM zone corresponding to the given lat/lon.

    Args:
        lat (float): Latitude in decimal degrees.
        lon (float): Longitude in decimal degrees.

    Returns:
        str: EPSG code string in the format "EPSG:326##" or "EPSG:327##"
    """
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Invalid latitude or longitude values.")

    # lon of exactly 180 would otherwise land in a non-existent zone 61.
    zone_number = min(int((lon + 180) / 6) + 1, 60)
    hemisphere_code = 326 if lat >= 0 else 327
    epsg_code = f"EPSG:{hemisphere_code}{zone_number:02d}"

    return epsg_code


def get_wgs84_info(in_raster: Path) -> tuple[bool, float | None, float | None]:
    """Returns WGS84 status and mean coordinates if the input raster is in WGS84.

    Args:
        in_raster (Path): Path to input raster dataset.

    Returns:
        tuple[bool, float | None, float | None]: A tuple containing:
            - bool: True if the input raster is in WGS84, False otherwise
            - float | None: Mean x coordinate (longitude) if WGS84, None otherwise
            - float | None: Mean y coordinate (latitude) if WGS84, None otherwise
    """
    with rasterio.open(in_raster) as src:
        if src.crs and src.crs.to_epsg() == 4326:
            mean_x = src.bounds.left + (src.bounds.right - src.bounds.left) / 2
            mean_y = src.bounds.bottom + (src.bounds.top - src.bounds.bottom) / 2
            return True, mean_x, mean_y
        return False, None, None
