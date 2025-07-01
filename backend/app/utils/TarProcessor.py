import logging
import tarfile
import os
from typing import Any, Dict, List

from PIL import Image


logger = logging.getLogger(__name__)

MAX_WIDTH = 1200
QUALITY = 80


class TarProcessor:
    """
    Used to extract contents of tar file and return tar file's directory structure
    in Dict format.
    """

    def __init__(self, tar_file_path: str) -> None:
        """Initialize TarProcessor with tar file path.

        Args:
            tar_file_path (str): Tar file path.
        """
        # confirm file exists
        if not os.path.exists(tar_file_path):
            raise FileNotFoundError(f"Unable to locate .tar at: {tar_file_path}")

        self.tar_file_path = tar_file_path

    def extract(self) -> None:
        """
        Extracts all contents of tar file to current directory and converts images to WebP.
        """
        with tarfile.open(self.tar_file_path, "r") as tar_file:
            parent_dir = os.path.dirname(self.tar_file_path)
            tar_file.extractall(path=parent_dir)

        # Convert images to WebP after extraction
        self._convert_images_in_directory(parent_dir)

    def _is_image_file(self, file_path: str) -> bool:
        """Check if a file is an image based on its extension.

        Args:
            file_path (str): Path to the file to check.

        Returns:
            bool: True if the file is an image, False otherwise.
        """
        image_extensions = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
        _, ext = os.path.splitext(file_path)
        return ext in image_extensions

    def _convert_images_in_directory(self, directory_path: str) -> None:
        """Walk through directory and convert all image files to WebP.

        Args:
            directory_path (str): Path to the directory to process.
        """
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                if self._is_image_file(file_path):
                    try:
                        convert_to_webp(file_path)
                    except Exception as e:
                        logger.error(f"Failed to convert {file_path}: {str(e)}")
                        # Continue processing other files even if one fails

    def get_directory_structure(self) -> Dict[str, Any]:
        """Returns directory structure of extracted files in Dict format.

        Note: This reads from the extracted filesystem, not the original tar file,
        so it will reflect any file conversions (e.g., images converted to WebP).

        Returns:
            dict: Dict representation of the extracted directory structure.
        """
        parent_dir = os.path.dirname(self.tar_file_path)
        return generate_filesystem_structure_json(parent_dir)

    def remove(self) -> None:
        """
        Remove .tar file from file system.
        """
        if os.path.exists(self.tar_file_path):
            os.remove(self.tar_file_path)


def generate_filesystem_structure_json(base_path: str) -> Dict[str, Any]:
    """Returns Dict representation of the filesystem directory structure.

    Args:
        base_path (str): Path to the base directory to analyze.

    Returns:
        dict: Dict representation of the filesystem directory structure.
    """

    def build_filesystem_tree(path: str) -> Dict[str, Any]:
        """Recursively builds the directory tree structure from filesystem.

        Args:
            path (str): Path to the current directory or file.

        Returns:
            Dict[str, Any]: Dictionary of directory/file structure.
        """
        node: Dict[str, Any] = {
            "name": os.path.basename(path),
            "type": "directory" if os.path.isdir(path) else "file",
        }

        if os.path.isfile(path):
            node["size"] = os.path.getsize(path)
        elif os.path.isdir(path):
            try:
                children = []
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    children.append(build_filesystem_tree(item_path))

                if children:
                    node["children"] = children
            except PermissionError:
                logger.error(f"Permission denied accessing directory: {path}")

        return node

    try:
        if not os.path.exists(base_path):
            return {"error": f"Directory does not exist: {base_path}"}

        # List all items in the base directory
        items = os.listdir(base_path)

        if len(items) == 0:
            return {"error": "Directory is empty"}

        # Check for single top-level directory (similar to tar logic)
        directories = [
            item for item in items if os.path.isdir(os.path.join(base_path, item))
        ]

        if len(directories) == 1 and len(items) == 1:
            # Single top-level directory case
            top_level_dir = os.path.join(base_path, directories[0])
            return build_filesystem_tree(top_level_dir)
        elif len(items) > 1:
            return {"error": "Multiple top-level items found in extracted directory"}
        else:
            # Single item that might not be a directory
            single_item = os.path.join(base_path, items[0])
            return build_filesystem_tree(single_item)

    except Exception as e:
        return {"error": f"Error reading filesystem: {e}"}


def convert_to_webp(image_path: str) -> str:
    """Convert an image file to WebP format with optional resizing.

    Args:
        image_path (str): Path to the source image file.

    Returns:
        str: Path to the converted WebP file.

    Raises:
        Exception: If image conversion fails.
    """
    try:
        with Image.open(image_path) as img:
            # Resize image if width is greater than MAX_WIDTH
            if img.width > MAX_WIDTH:
                new_height = int((MAX_WIDTH / img.width) * img.height)
                img = img.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)

            # Create output path by replacing extension with .webp
            base_path = os.path.splitext(image_path)[0]
            output_path = f"{base_path}.webp"

            # Convert to RGB if necessary (WebP doesn't support all modes)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            img.save(output_path, "WEBP", quality=QUALITY)

        # Remove original image only after successful conversion
        os.remove(image_path)

        return output_path

    except Exception as e:
        raise Exception(f"Failed to convert {image_path} to WebP: {str(e)}")
