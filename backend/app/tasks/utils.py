import re
import secrets
from pathlib import Path


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
