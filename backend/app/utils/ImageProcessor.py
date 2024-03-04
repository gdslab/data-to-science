import logging
import json
import multiprocessing
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, NoReturn

from pydantic import ValidationError

from app.utils.STACProperties import (
    ImageStructure,
    Metadata,
    STACProperties,
    STACPropertiesValidator,
    Stats,
)

logger = logging.getLogger("__name__")


class ImageProcessor:
    """
    Used to process uploaded rasters in the GeoTIFF format. If the raster is not
    using the Cloud Optimized GeoTIFF (COG) layout, one will be generated. An additional
    compressed COG for visualization will be created along with a small preview image.
    """

    def __init__(self, in_raster: str, output_dir: str | Path | None = None) -> None:
        self.in_raster = Path(in_raster)

        if not output_dir:
            output_dir = self.in_raster.parents[1]

        self.out_dir = Path(output_dir)
        self.out_raster = self.out_dir / self.in_raster.name
        self.preview_out_path = self.out_raster.with_suffix(".jpg")

        self.stac_properties: STACProperties = {"raster": [], "eo": []}

    def run(self) -> Path:
        info: dict = get_info(self.in_raster)

        if is_cog(info):
            shutil.move(self.in_raster, self.out_dir)
        else:
            convert_to_cog(self.in_raster, self.out_raster, info)

        if os.path.exists(self.in_raster.parent):
            shutil.rmtree(self.in_raster.parent)

        self.stac_properties = get_stac_properties(info)

        create_preview_image(
            self.out_raster, self.preview_out_path, self.stac_properties
        )

        return self.out_raster

    def get_default_symbology(self) -> dict | NoReturn:
        """Creates default symbology settings based on raster type and stats."""
        if (
            len(self.stac_properties["raster"]) > 0
            and len(self.stac_properties["eo"]) > 0
        ):
            if len(self.stac_properties["raster"]) == 1:
                stats: Stats | None = self.stac_properties["raster"][0].get("stats")
                if stats is None:
                    raise Exception("Unable to get raster stats")

                return {
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

                return {"settings": symbology}
            else:
                raise Exception("Need at least three bands for ortho imagery")
        else:
            raise Exception(
                "Cannot get default symbology settings before running processor"
            )


def get_info(in_raster: Path) -> dict | NoReturn:
    """Returns output from gdalinfo -json <input_dataset>.

    Args:
        in_raster (Path): Path to input dataset

    Raises:
        e: Raise exception

    Returns:
        dict: _description_
    """
    result: subprocess.CompletedProcess = subprocess.run(
        ["gdalinfo", "-approx_stats", "-json", in_raster],
        stdout=subprocess.PIPE,
        check=True,
    )
    result.check_returncode()
    try:
        gdalinfo: dict = json.loads(result.stdout)
    except Exception as e:
        logging.error(str(e))
        raise e
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


def convert_to_cog(
    in_raster: Path, out_raster: Path, info: dict, num_threads: int | None = None
) -> None:
    """Runs gdalwarp to generate new raster in COG layout.

    Args:
        in_raster (Path): Path to input raster dataset
        out_raster (Path): Path for output raster dataset
        info (dict): gdalinfo -json output
        num_threads (int | None, optional): No. of CPUs to use. Defaults to None.
    """
    if not num_threads:
        num_threads = int(multiprocessing.cpu_count() / 2)

    result: subprocess.CompletedProcess = subprocess.run(
        [
            "gdalwarp",
            in_raster,
            out_raster,
            "-of",
            "COG",
            "-co",
            "COMPRESS=DEFLATE",
            "-co",
            f"NUM_THREADS={num_threads}",
            "-co",
            "BIGTIFF=YES",
            "-wm",
            "500",
        ]
    )

    result.check_returncode()


def create_preview_image(
    in_raster: Path, preview_out_path: Path, stac_props: STACProperties
) -> None:
    """Generates preview image for GeoTIFF data products.

    Args:
        in_raster (Path): Path to input dataset.
        preview_out_path (Path): Path for preview image.
        stac_props (STACProperties): gdalinfo STAC output.
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

    size_params: list = ["-outsize", "6.25%", "6.25%"]
    inout_params: list = [in_raster, preview_out_path]

    command = ["gdal_translate", "-of", "JPEG", "-ot", "Byte", "-co", "QUALITY=75"]
    command.extend(band_params)
    command.extend(size_params)
    command.extend(scale_params)
    command.extend(inout_params)

    result = subprocess.run(command)

    result.check_returncode()
