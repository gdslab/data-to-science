from pathlib import Path

import pytest

from app.api.utils import get_file_extension


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("a.tif", ".tif"),
        ("a.tiff", ".tif"),
        ("A.TIF", ".tif"),
        ("A.TIFF", ".tif"),
        ("a.copc.laz", ".copc.laz"),
        ("a.LAZ", ".laz"),
        ("a.las", ".las"),
        ("a.zip", ".zip"),
        ("a.ply", ".ply"),
        ("a.txt", ".txt"),
    ],
)
def test_get_file_extension(filename: str, expected: str) -> None:
    assert get_file_extension(Path(filename)) == expected
