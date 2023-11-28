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

    def __init__(self, img_path):
        self.img_path = img_path

        output_dir = os.path.dirname(self.img_path)
        output_name = os.path.basename(self.img_path).replace("__temp", "")

        self.out_path = os.path.join(output_dir, output_name)
        self.preview_out_path = os.path.join(
            output_dir, output_name.replace("tif", "webp")
        )

        self.stac_properties = {"raster": [], "eo": []}

    def run(self):
        info = get_info(self.img_path)
        if is_cog(info):
            shutil.move(self.img_path, self.out_path)
            convert_to_cog(self.img_path, self.out_path, info, vis_only=True)
        else:
            convert_to_cog(self.img_path, self.out_path, info)

        os.remove(self.img_path)
        if os.path.exists(self.img_path + ".aux.xml"):
            os.remove(self.img_path + ".aux.xml")

        create_preview_webp(self.out_path, self.preview_out_path, info)

        self.stac_properties = get_stac_properties(info)

        return self.out_path

    def get_default_symbology(self) -> dict:
        """Creates default symbology settings based on raster type and stats."""
        if (
            len(self.stac_properties["raster"]) > 0
            and len(self.stac_properties["eo"]) > 0
        ):
            if len(self.stac_properties["raster"]) == 1:
                stats = self.stac_properties["raster"][0].get("stats")

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
                symbology: OrthoSymbology = {
                    "mode": "minMax",
                    "meanStdDev": 2,
                    "red": {},
                    "green": {},
                    "blue": {},
                }

                for idx, band in enumerate(["red", "green", "blue"]):
                    stats = self.stac_properties["raster"][idx]
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
    result = subprocess.run(
        ["gdalinfo", "-stats", "-hist", "-json", img_path],
        stdout=subprocess.PIPE,
        check=True,
    )
    result.check_returncode()
    try:
        gdalinfo = json.loads(result.stdout)
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
        metadata = info.get("metadata")
        if type(metadata) is dict and metadata.get("IMAGE_STRUCTURE"):
            image_struct = metadata.get("IMAGE_STRUCTURE")
            if type(image_struct) is dict and image_struct.get("LAYOUT"):
                layout = image_struct.get("LAYOUT")
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
        stac = info.get("stac")
        if type(stac) is dict and stac.get("raster:bands") and stac.get("eo:bands"):
            try:
                stac_properties = STACPropertiesValidator.validate_python(
                    {"raster": stac.get("raster:bands"), "eo": stac.get("eo:bands")}
                )
            except ValidationError as e:
                logger.error(e)
            except Exception as e:
                logger.error(e)

    return stac_properties


def get_band_count(info: dict) -> int:
    """Return number of bands in raster. If unable to determine
    number of bands, treat as a single band raster and return 1.

    Args:
        info (dict): gdalinfo -json output

    Returns:
        int: Number of bands
    """
    if info and info.get("bands"):
        bands = info.get("bands")
        if type(bands) is list:
            return len(bands)
    return 1


def convert_to_cog(
    img_path: str,
    out_path: str,
    info: dict,
    num_threads: int | None = None,
    vis_only: bool = False,
) -> None:
    """Runs gdalwarp to generate new raster in COG layout.

    Args:
        img_path (str): Path to input raster dataset
        out_path (str): Path for output raster dataset
        info (dict): gdalinfo -json output
        num_threads (int | None, optional): No. of CPUs to use. Defaults to None.
        vis_only (bool, optional): Skips generating COG if True. Defaults to False.
    """
    if not num_threads:
        num_threads = int(multiprocessing.cpu_count() / 2)
    # uncompressed COG for processing
    if not vis_only:
        result = subprocess.run(
            [
                "gdalwarp",
                img_path,
                out_path,
                "-of",
                "COG",
                "-co",
                f"NUM_THREADS={num_threads}",
                "-co",
                "BIGTIFF=YES",
                "-wm",
                "500",
            ]
        )
    # compressed COG for visualization
    if get_band_count(info) < 3:
        compression = "DEFLATE"
    else:
        compression = "DEFLATE"
    result = subprocess.run(
        [
            "gdalwarp",
            img_path,
            out_path[:-4] + "_web.tif",
            "-of",
            "COG",
            "-co",
            f"COMPRESS={compression}",
            "-co",
            "QUALITY=75",
            "-co",
            f"NUM_THREADS={num_threads}",
            "-co",
            "BIGTIFF=YES",
            "-wm",
            "500",
        ]
    )
    result.check_returncode()


def create_preview_webp(img_path: str, out_path: str, info: dict) -> None:
    """Generates preview image in WEBP format for multiband datasets and JPEG
    for single band datasets.

    Args:
        img_path (str): Path to input dataset
        out_path (str): Path for output dataset
        info (dict): gdalinfo -json output
    """
    band_count = get_band_count(info)
    if band_count == 3 or band_count == 4:
        result = subprocess.run(
            [
                "gdal_translate",
                "-of",
                "WEBP",
                "-co",
                "QUALITY=75",
                "-b",
                "1",
                "-b",
                "2",
                "-b",
                "3",
                img_path,
                out_path,
                "-outsize",
                "6.25%",
                "6.25%",
            ]
        )
    else:
        result = subprocess.run(
            [
                "gdal_translate",
                "-scale",
                "-of",
                "JPEG",
                "-co",
                "QUALITY=75",
                "-b",
                "1",
                img_path,
                out_path,
                "-outsize",
                "6.25%",
                "6.25%",
            ]
        )
    result.check_returncode()
