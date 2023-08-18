import json
import multiprocessing
import os
import shutil
import subprocess


class ImageProcessor:
    """Used to process uploaded GeoTIFF rasters and convert to COG if necessary."""

    def __init__(self, img_path):
        self.img_path = img_path

        output_dir = os.path.dirname(self.img_path)
        output_name = os.path.basename(self.img_path).replace("__temp", "")

        self.out_path = os.path.join(output_dir, output_name)
        self.preview_out_path = os.path.join(
            output_dir, output_name.replace("tif", "webp")
        )

    def run(self):
        if is_cog(self.img_path):
            shutil.move(self.img_path, self.out_path)
        else:
            convert_to_cog(self.img_path, self.out_path)

        os.remove(self.img_path)

        create_preview_webp(self.out_path, self.preview_out_path)

        return self.out_path


def is_cog(img_path: str) -> bool:
    """Checks gdalinfo json output for 'COG' layout."""
    result = subprocess.run(
        ["gdalinfo", "-json", img_path], stdout=subprocess.PIPE, check=True
    )
    result.check_returncode()
    try:
        gdalinfo_json = json.loads(result.stdout)
    except Exception as e:
        print("Unable to load json output into dictionary")
        raise e
    if gdalinfo_json.get("metadata").get("IMAGE_STRUCTURE").get("LAYOUT") == "COG":
        return True
    else:
        return False


def convert_to_cog(
    img_path: str, out_path: str, num_threads: int | None = None
) -> None:
    """Converts GeoTIFF to a COG."""
    if not num_threads:
        num_threads = int(multiprocessing.cpu_count() / 2)
    result = subprocess.run(
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


def create_preview_webp(img_path: str, out_path: str) -> None:
    """Generates preview image in WEBP format from original image."""
    result = subprocess.run(
        [
            "gdal_translate",
            "-of",
            "WEBP",
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
    result.check_returncode()
