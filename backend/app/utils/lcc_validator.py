"""LCC zip file validation and unpacking utility."""

import zipfile
from pathlib import Path
from typing import Union


def unpack_lcc_zip(zip_path: Union[str, Path], output_dir: Union[str, Path]) -> str:
    """
    Validates and unpacks an LCC zip file.

    Checks that the zip contains the required files (*.lcc, index.bin, data.bin)
    before extracting. Only extracts if all required files are present.

    Args:
        zip_path: Path to the zip file to validate and unpack.
        output_dir: Directory where contents will be extracted.

    Returns:
        Full path to the extracted .lcc file.

    Raises:
        FileNotFoundError: If zip_path does not exist.
        zipfile.BadZipFile: If the file is not a valid zip archive.
        ValueError: If required files are missing or multiple .lcc files found.
    """
    zip_path = Path(zip_path)
    output_dir = Path(output_dir)

    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()

        # Try to find required files, first in root, then in a single top-level directory
        prefix, lcc_files = _find_required_files(names)

        # All checks passed, extract
        output_dir.mkdir(parents=True, exist_ok=True)
        _extract_with_prefix(zf, output_dir, prefix)

    # Return full path to the .lcc file
    lcc_filename = lcc_files[0]
    return str(output_dir / lcc_filename)


def _extract_with_prefix(zf: zipfile.ZipFile, output_dir: Path, prefix: str) -> None:
    """
    Extract files from zip, stripping the prefix from paths.

    Args:
        zf: Open ZipFile object.
        output_dir: Directory to extract to.
        prefix: Prefix to strip from file paths ("" for root, "dirname/" for subdirectory).
    """
    for member in zf.namelist():
        # Skip directory entries and files not under the prefix
        if member.endswith("/"):
            continue
        if prefix and not member.startswith(prefix):
            continue

        # Strip prefix to get target path
        target_name = member[len(prefix):] if prefix else member
        target_path = output_dir / target_name

        # Create parent directories if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Extract file
        with zf.open(member) as src, open(target_path, "wb") as dst:
            dst.write(src.read())


def _find_required_files(names: list[str]) -> tuple[str, list[str]]:
    """
    Find required LCC files in the zip archive.

    Args:
        names: List of file names from the zip archive.

    Returns:
        Tuple of (prefix, lcc_files) where prefix is "" for root or "dirname/" for subdirectory.

    Raises:
        ValueError: If required files are missing or multiple .lcc files found.
    """
    # First, check root
    lcc_files, missing = _check_location(names, "")
    if not missing:
        if len(lcc_files) > 1:
            raise ValueError(
                f"Multiple .lcc files found: {', '.join(lcc_files)}. Expected exactly one."
            )
        return "", lcc_files

    # Find top-level directories
    top_dirs = set()
    for name in names:
        if "/" in name:
            top_dir = name.split("/")[0] + "/"
            top_dirs.add(top_dir)

    # Check if there's a single top-level directory
    if len(top_dirs) == 1:
        prefix = list(top_dirs)[0]
        lcc_files, missing = _check_location(names, prefix)
        if not missing:
            if len(lcc_files) > 1:
                raise ValueError(
                    f"Multiple .lcc files found in {prefix}: {', '.join(lcc_files)}. Expected exactly one."
                )
            return prefix, lcc_files

    # If we get here, files are missing
    raise ValueError(f"Missing required files: {', '.join(missing)}")


def _check_location(names: list[str], prefix: str) -> tuple[list[str], list[str]]:
    """
    Check for required files at a given location prefix.

    Args:
        names: List of file names from the zip archive.
        prefix: Path prefix to check ("" for root, "dirname/" for subdirectory).

    Returns:
        Tuple of (lcc_files, missing) where lcc_files is list of .lcc filenames
        and missing is list of missing required file descriptions.
    """
    # Find .lcc files at this location
    lcc_files = []
    for name in names:
        if not name.endswith(".lcc"):
            continue
        # Strip prefix and check it's directly at this level (no further slashes)
        if prefix:
            if name.startswith(prefix):
                remainder = name[len(prefix):]
                if "/" not in remainder:
                    lcc_files.append(remainder)
        else:
            if "/" not in name:
                lcc_files.append(name)

    has_index_bin = f"{prefix}index.bin" in names
    has_data_bin = f"{prefix}data.bin" in names

    missing = []
    if not lcc_files:
        missing.append("*.lcc file")
    if not has_index_bin:
        missing.append("index.bin")
    if not has_data_bin:
        missing.append("data.bin")

    return lcc_files, missing
