import logging
import json
import multiprocessing
import os
import shutil
import subprocess

from pydantic import ValidationError

from app.utils.STACProperties import STACProperties, STACPropertiesValidator

logger = logging.getLogger("__name__")


class ImageProcessor:
    """
    Used to process uploaded rasters in the GeoTIFF format. If the raster is not
    using the Cloud Optimized GeoTIFF (COG) layout, one will be generated. An additional
    compressed COG for visualization will be created along with a small preview image.
    """

    def __init__(self, img_path: str, output_dir: str | None = None) -> None:
        self.img_path: str = img_path

        if not output_dir:
            output_dir: str = os.path.dirname(self.img_path)

        output_name = os.path.basename(self.img_path).replace("__temp", "")

        self.out_path: str = os.path.join(output_dir, output_name)
        self.preview_out_path: str = os.path.join(
            output_dir, output_name.replace("tif", "jpg")
        )

        self.stac_properties: dict = {"raster": [], "eo": []}

    def run(self) -> str:
        info: dict = get_info(self.img_path)
        if is_cog(info):
            shutil.move(self.img_path, self.out_path)
        else:
            convert_to_cog(self.img_path, self.out_path, info)

        if os.path.exists(self.img_path):
            os.remove(self.img_path)

        if os.path.exists(self.img_path + ".aux.xml"):
            os.remove(self.img_path + ".aux.xml")

        self.stac_properties = get_stac_properties(info)

        create_preview_image(self.out_path, self.preview_out_path, self.stac_properties)

        return self.out_path

    def get_default_symbology(self) -> dict:
        """Creates default symbology settings based on raster type and stats."""
        if (
            len(self.stac_properties["raster"]) > 0
            and len(self.stac_properties["eo"]) > 0
        ):
            if len(self.stac_properties["raster"]) == 1:
                stats: dict = self.stac_properties["raster"][0].get("stats")

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
                    stats: dict = self.stac_properties["raster"][idx]["stats"]
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


def get_info(img_path: str) -> dict:
    """Returns output from gdalinfo -json <input_dataset>.

    Args:
        img_path (str): Path to input dataset

    Raises:
        e: Raise exception

    Returns:
        dict: _description_
    """
    result: subprocess.CompletedProcess = subprocess.run(
        ["gdalinfo", "-approx_stats", "-json", img_path],
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
        metadata: dict = info.get("metadata")
        if type(metadata) is dict and metadata.get("IMAGE_STRUCTURE"):
            image_struct: dict = metadata.get("IMAGE_STRUCTURE")
            if type(image_struct) is dict and image_struct.get("LAYOUT"):
                layout: str = image_struct.get("LAYOUT")
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
        stac: dict = info.get("stac")
        if type(stac) is dict and stac.get("raster:bands") and stac.get("eo:bands"):
            try:
                stac_properties: STACProperties = (
                    STACPropertiesValidator.validate_python(
                        {"raster": stac.get("raster:bands"), "eo": stac.get("eo:bands")}
                    )
                )
            except ValidationError as e:
                logger.error(e)
            except Exception as e:
                logger.error(e)

    return stac_properties


def convert_to_cog(
    img_path: str, out_path: str, info: dict, num_threads: int | None = None
) -> None:
    """Runs gdalwarp to generate new raster in COG layout.

    Args:
        img_path (str): Path to input raster dataset
        out_path (str): Path for output raster dataset
        info (dict): gdalinfo -json output
        num_threads (int | None, optional): No. of CPUs to use. Defaults to None.
    """
    if not num_threads:
        num_threads: int = int(multiprocessing.cpu_count() / 2)

    result: subprocess.CompletedProcess = subprocess.run(
        [
            "gdalwarp",
            img_path,
            out_path,
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
    img_path: str, out_path: str, stac_props: STACProperties
) -> None:
    """Generates preview image for GeoTIFF data products.

    Args:
        img_path (str): Path to input dataset
        out_path (str): Path for output dataset
        stac_props (STACProperties): gdalinfo STAC output
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
        band_params: list = ["-b", "1"]
        scale_params: list = [
            "-scale_1",
            str(stac_props["raster"][0]["stats"]["minimum"]),
            str(stac_props["raster"][0]["stats"]["maximum"]),
            "0",
            "255",
        ]

    size_params: list = ["-outsize", "6.25%", "6.25%"]
    inout_params: list = [img_path, out_path]

    command = ["gdal_translate", "-of", "JPEG", "-ot", "Byte", "-co", "QUALITY=75"]
    command.extend(band_params)
    command.extend(size_params)
    command.extend(scale_params)
    command.extend(inout_params)

    result = subprocess.run(command)

    result.check_returncode()
