import re
import secrets
from pathlib import Path
from typing import Dict, Tuple, Union
from PIL import Image


def is_valid_filename(filename: str) -> bool:
    """Check if a filename is valid.

    Args:
        filename (str): Filename to check.

    Returns:
        bool: True if filename is valid, False otherwise.
    """
    try:
        Path(filename)
        return True
    except ValueError:
        return False


def get_safe_filename_prefix(input_string: str, length: int = 5) -> str:
    """Extract a safe prefix from a string for use in filenames.

    Args:
        input_string (str): Input string to extract prefix from.
        length (int): Length of prefix to extract (default: 5).

    Returns:
        str: Safe prefix string of specified length.
    """
    # Remove all non-alphanumeric characters except underscores and hyphens
    sanitized = re.sub(r"[^\w\-_]", "_", input_string).strip("_")

    # If string is empty after sanitization, generate a random string
    if not sanitized:
        sanitized = secrets.token_urlsafe(length)

    # Take first n characters
    prefix = sanitized[:length]

    # Ensure the prefix is valid for filenames
    if not is_valid_filename(prefix):
        prefix = f"safe_{prefix}"

    return prefix


def validate_panoramic_image(
    image_path: str,
) -> Tuple[bool, Union[str, Dict[str, Union[str, int]]]]:
    """Validate a panoramic image.

    Args:
        image_path (str): Path to panoramic image.

    Returns:
        bool: True if image is valid, False otherwise.
    """
    # Accepted formats
    accepted_formats = {"JPEG", "PNG", "WEBP", "AVIF", "MPO"}

    try:
        with Image.open(image_path) as img:
            fmt = img.format or ""
            if fmt not in accepted_formats:
                return False, f"Image format not supported (got {fmt})"

            # If format is MPO, jump to the first JPEG frame
            if fmt == "MPO":
                img.seek(0)

            width, height = img.size
            aspect_ratio = width / height

            if abs(aspect_ratio - 2.0) > 0.1:
                return False, f"Image is not 2:1 (got {aspect_ratio:.2f}:1)"
            if width < 2048:
                return False, f"Image width too small (got {width}px)"

            return True, {"format": fmt, "width": width, "height": height}

    except Exception:
        return False, "Image is not a valid panoramic image"
