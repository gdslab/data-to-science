import logging
import tarfile
import os
import shutil

from PIL import Image


logger = logging.getLogger(__name__)

MAX_WIDTH = 1200
QUALITY = 80


class TarProcessor:
    """
    Used to extract contents of tar file, convert images to WebP format,
    and store them in an "images" directory while discarding the original
    tar contents.
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
        Extracts all contents of tar file, converts images to WebP,
        stores them in an "images" directory, and cleans up extracted contents.
        """
        parent_dir = os.path.dirname(self.tar_file_path)
        images_dir = os.path.join(parent_dir, "images")

        # Create images directory if it doesn't exist
        os.makedirs(images_dir, exist_ok=True)

        # Create temporary extraction directory
        temp_extract_dir = os.path.join(parent_dir, "temp_extract")

        try:
            # Extract tar file to temporary directory
            with tarfile.open(self.tar_file_path, "r") as tar_file:
                tar_file.extractall(path=temp_extract_dir)

            # Convert images and move to images directory
            self._process_images_to_images_dir(temp_extract_dir, images_dir)

        finally:
            # Clean up temporary extraction directory
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)

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

    def _process_images_to_images_dir(self, source_dir: str, images_dir: str) -> None:
        """Walk through source directory, convert all image files to WebP, and move to images directory.

        Args:
            source_dir (str): Path to the source directory to process.
            images_dir (str): Path to the images directory where WebP files will be stored.

        Raises:
            Exception: If there are filename conflicts (duplicate filenames).
        """
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if self._is_image_file(file_path):
                    try:
                        # Convert to WebP in place first
                        webp_path = convert_to_webp(file_path)

                        # Preserve original filename with .webp extension
                        original_base_name = os.path.splitext(file)[0]
                        webp_filename = f"{original_base_name}.webp"
                        destination_path = os.path.join(images_dir, webp_filename)

                        # Check for filename conflicts
                        if os.path.exists(destination_path):
                            raise Exception(
                                f"Filename conflict: '{webp_filename}' already exists in images directory"
                            )

                        # Move WebP file to images directory
                        shutil.move(webp_path, destination_path)

                    except Exception as e:
                        logger.error(f"Failed to process {file_path}: {str(e)}")
                        # Re-raise the exception to stop processing on conflicts or other critical errors
                        raise

    def get_images_directory_path(self) -> str:
        """Returns the path to the images directory.

        Returns:
            str: Path to the images directory.
        """
        parent_dir = os.path.dirname(self.tar_file_path)
        return os.path.join(parent_dir, "images")

    def remove(self) -> None:
        """
        Remove .tar file from file system.
        """
        if os.path.exists(self.tar_file_path):
            os.remove(self.tar_file_path)


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
