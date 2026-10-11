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
# A low zoom tile reads the coarsest overview whole, so cap how large that level
# may be before a COG layout upload is rewritten with a full pyramid.
MAX_COARSEST_LEVEL_DIMENSION = 2048
# Fewest bands that can make up an RGB composite.
MIN_RGB_BANDS = 3
# GDAL reads an alpha band as a mask only when it has one of these types. Any
# other alpha band is written to the COG's mask band instead, which readers honor.
MASK_ALPHA_TYPES = ("Byte", "UInt16")


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

        # The COG driver's warp adds an alpha band in the raster's own type and
        # drops any mask band, so warp through a VRT when the result needs a mask.
        source = self.in_raster
        if epsg_code and needs_mask_after_warp(info):
            logger.info(f"Projecting raster to {epsg_code}")
            source = warp_to_vrt(self.in_raster, epsg_code, self.resampling)
            info = get_info(source, with_stats=False)
            epsg_code = None

        mask_band = alpha_band_without_mask(info)

        # A COG still has to be rewritten when it needs reprojecting, when its
        # overview pyramid is too shallow to serve low zoom tiles, or when its
        # alpha band has to move into the mask band.
        if (
            is_cog(info)
            and has_complete_pyramid(info)
            and not epsg_code
            and mask_band is None
        ):
            logger.info("Raster is in COG layout, moving to output directory")
            shutil.move(self.in_raster, self.out_dir)
        else:
            if mask_band is not None:
                logger.info("Writing alpha band as the mask band")
            elif is_cog(info) and not epsg_code:
                logger.info("COG has no usable overview pyramid, rewriting")
            else:
                logger.info("Converting raster to COG layout")
            convert_to_cog(
                source,
                self.out_raster,
                self.resampling,
                epsg_code,
                mask_band=mask_band,
                band_count=len(info.get("bands", [])),
            )

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
            if is_single_band(len(self.stac_properties["raster"])):
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
            else:
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
            raise Exception(
                "Cannot get default symbology settings before running processor"
            )


def is_single_band(band_count: int) -> bool:
    """Returns True if a raster is displayed as a single band.

    An RGB composite needs three bands, so a raster with fewer than that is
    displayed as band 1 with a color ramp. Two band rasters carry their second
    band as an alpha channel, which titiler reads as the tile mask rather than as
    data, so band 1 is the only band worth displaying either way.

    Args:
        band_count (int): Number of bands in the raster.

    Returns:
        bool: True when the raster has one or two bands.
    """
    return 0 < band_count < MIN_RGB_BANDS


def resampling_for(band_count: int) -> str:
    """Returns the resampling method to use for a raster.

    Args:
        band_count (int): Number of bands in the raster.

    Returns:
        str: GDAL resampling method name.
    """
    return MULTIBAND_RESAMPLING if band_count >= MIN_RGB_BANDS else DEFAULT_RESAMPLING


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


def has_complete_pyramid(info: dict) -> bool:
    """Return True if the coarsest level is small enough to serve tiles from.

    The coarsest level is the smallest overview, or the full raster when it has
    none. Missing size or band information counts as incomplete.

    Args:
        info (dict): gdalinfo -json output

    Returns:
        bool: True if every band's coarsest level fits the dimension limit
    """
    size = info.get("size") if info else None
    bands = info.get("bands") if info else None
    if not size or not bands:
        return False

    for band in bands:
        levels = [ov["size"] for ov in band.get("overviews", []) if ov.get("size")]
        coarsest = min(levels, key=max) if levels else size
        if max(coarsest) > MAX_COARSEST_LEVEL_DIMENSION:
            return False

    return True


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


def alpha_band_without_mask(info: dict) -> int | None:
    """Returns the index of an alpha band that GDAL does not read as a mask.

    Args:
        info (dict): gdalinfo -json output

    Returns:
        int | None: One-based band index, or None when there is no such band.
    """
    bands = info.get("bands", []) if info else []
    for band in bands:
        if band.get("colorInterpretation") == "Alpha":
            flags = bands[0].get("mask", {}).get("flags", [])
            return None if "ALPHA" in flags else band["band"]
    return None


def needs_mask_after_warp(info: dict) -> bool:
    """Returns True if reprojecting with the COG driver would leave an alpha band
    that GDAL does not read as a mask.

    The driver adds an alpha band in the raster's own type when the raster has no
    nodata value, and drops any mask band the raster already has.

    Args:
        info (dict): gdalinfo -json output

    Returns:
        bool: True when the reprojected raster needs a mask band.
    """
    bands = info.get("bands", []) if info else []
    if not bands:
        return False
    if alpha_band_without_mask(info) is not None:
        return True
    return (
        bands[0].get("type") not in MASK_ALPHA_TYPES and "noDataValue" not in bands[0]
    )


def build_warp_command(
    in_raster: Path, out_vrt: Path, resampling: str, epsg_code: str
) -> List[str]:
    """Returns the gdalwarp command used to reproject a raster to a VRT.

    Args:
        in_raster (Path): Path to input raster dataset.
        out_vrt (Path): Path for the output VRT.
        resampling (str): Resampling method for warping.
        epsg_code (str): Target EPSG code.

    Returns:
        List[str]: Command and arguments for gdalwarp.
    """
    return [
        "gdalwarp",
        "-of",
        "VRT",
        "-t_srs",
        epsg_code,
        "-r",
        resampling,
        "-dstalpha",
        str(in_raster),
        str(out_vrt),
    ]


def warp_to_vrt(in_raster: Path, epsg_code: str, resampling: str) -> Path:
    """Reprojects a raster to a VRT whose last band is an alpha band.

    Args:
        in_raster (Path): Path to input raster dataset.
        epsg_code (str): Target EPSG code.
        resampling (str): Resampling method for warping.

    Returns:
        Path: Path to the VRT, written next to the input raster.
    """
    out_vrt = in_raster.with_suffix(".vrt")
    run_gdal(build_warp_command(in_raster, out_vrt, resampling, epsg_code))
    return out_vrt


def build_cog_command(
    in_raster: Path,
    out_raster: Path,
    resampling: str = DEFAULT_RESAMPLING,
    epsg_code: str | None = None,
    num_threads: int | None = None,
    mask_band: int | None = None,
    band_count: int = 0,
) -> List[str]:
    """Returns the gdal_translate command used to write a COG.

    Args:
        in_raster (Path): Path to input raster dataset.
        out_raster (Path): Path for output raster dataset.
        resampling (str): Resampling method for warping and overviews.
        epsg_code (str | None): Target EPSG code, or None to keep the source CRS.
        num_threads (int | None, optional): No. of CPUs to use. Defaults to None.
        mask_band (int | None): Band written as the mask band instead of a data
            band, or None to keep every band.
        band_count (int): Number of bands in the input raster.

    Raises:
        ValueError: A mask band was requested together with reprojection.

    Returns:
        List[str]: Command and arguments for gdal_translate.
    """
    if mask_band and epsg_code:
        raise ValueError("The COG driver drops the mask band when it reprojects")

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
        "OVERVIEWS=IGNORE_EXISTING",
        "-co",
        f"NUM_THREADS={num_threads}",
        "-co",
        "BIGTIFF=IF_SAFER",
        "-co",
        "STATISTICS=YES",
    ]

    if mask_band:
        for band in range(1, band_count + 1):
            if band != mask_band:
                command.extend(["-b", str(band)])
        command.extend(["-mask", str(mask_band)])

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
    mask_band: int | None = None,
    band_count: int = 0,
) -> None:
    """Runs gdal_translate to generate new raster in COG layout.

    Args:
        in_raster (Path): Path to input raster dataset.
        out_raster (Path): Path for output raster dataset.
        resampling (str): Resampling method for warping and overviews.
        epsg_code (str | None): Target EPSG code, or None to keep the source CRS.
        num_threads (int | None, optional): No. of CPUs to use. Defaults to None.
        mask_band (int | None): Band written as the mask band instead of a data
            band, or None to keep every band.
        band_count (int): Number of bands in the input raster.
    """
    if epsg_code:
        logger.info(f"Projecting raster to {epsg_code}")

    run_gdal(
        build_cog_command(
            in_raster,
            out_raster,
            resampling,
            epsg_code,
            num_threads,
            mask_band=mask_band,
            band_count=band_count,
        )
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
    band_indexes = [1] if is_single_band(len(stac_props["raster"])) else [1, 2, 3]

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

    for band_index in band_indexes:
        command.extend(["-b", str(band_index)])

    command.extend(["-outsize", "320", "0"])

    # -scale_N refers to the output band position
    for position, band_index in enumerate(band_indexes, start=1):
        stats = stac_props["raster"][band_index - 1]["stats"]
        command.extend(
            [
                f"-scale_{position}",
                str(stats["minimum"]),
                str(stats["maximum"]),
                "0",
                "255",
            ]
        )

    command.extend([str(in_raster), str(preview_out_path)])

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
