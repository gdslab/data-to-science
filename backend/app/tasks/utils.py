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
