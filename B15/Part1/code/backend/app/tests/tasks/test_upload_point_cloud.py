"""Tests for the upload_point_cloud Celery task (las/laz to COPC via untwine)."""

import struct
import subprocess
from pathlib import Path
from unittest.mock import patch

import laspy
import numpy as np
from sqlalchemy.orm import Session

from app import crud
from app.schemas.job import Status
from app.tasks.upload_tasks import upload_point_cloud
from app.tests.utils.data_product import SampleDataProduct

POINT_COUNT = 1000


def create_test_las(las_path: Path, zero_header_bbox: bool = False) -> None:
    """Write a small LAS 1.4 (point format 7) file with RGB points.

    Args:
        las_path (Path): Destination for the LAS file.
        zero_header_bbox (bool): Zero out the header bounding box to mimic
            files whose generating software never set it. Points remain far
            from the origin, so the header no longer contains them.
    """
    rng = np.random.default_rng(42)
    header = laspy.LasHeader(point_format=7, version="1.4")
    header.offsets = [496000.0, 4475000.0, 0.0]
    header.scales = [0.001, 0.001, 0.001]
    las = laspy.LasData(header)
    las.x = rng.uniform(496533.0, 496684.0, POINT_COUNT)
    las.y = rng.uniform(4475638.0, 4475726.0, POINT_COUNT)
    las.z = rng.uniform(100.0, 157.0, POINT_COUNT)
    las.red = rng.integers(0, 65280, POINT_COUNT, dtype=np.uint16)
    las.green = rng.integers(0, 65280, POINT_COUNT, dtype=np.uint16)
    las.blue = rng.integers(0, 65280, POINT_COUNT, dtype=np.uint16)
    las.write(str(las_path))

    if zero_header_bbox:
        # bytes 179-226 of a LAS 1.4 header hold max/min x, y, z
        with open(las_path, "r+b") as f:
            f.seek(179)
            f.write(struct.pack("<6d", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))


def setup_upload_dirs(
    tmp_path: Path, filename: str = "upload.las"
) -> tuple[Path, Path, Path]:
    """Create the directory layout upload_point_cloud expects.

    Returns:
        tuple[Path, Path, Path]: Fake tusd storage path, destination las
            filepath inside a work subdirectory, and the data product
            directory that receives the COPC.
    """
    storage_path = tmp_path / "tusd" / filename
    storage_path.parent.mkdir()
    data_product_dir = tmp_path / "data_product"
    work_dir = data_product_dir / "tmp"
    work_dir.mkdir(parents=True)
    return storage_path, work_dir / filename, data_product_dir


def test_upload_point_cloud_success(db: Session, tmp_path: Path) -> None:
    """A valid LAS converts to a non-empty COPC and the job succeeds."""
    data_product = SampleDataProduct(db, data_type="point_cloud")
    storage_path, las_filepath, data_product_dir = setup_upload_dirs(tmp_path)
    create_test_las(storage_path)

    with patch("app.tasks.upload_tasks.get_db", side_effect=lambda: iter([db])):
        result = upload_point_cloud(
            str(storage_path),
            str(las_filepath),
            data_product.job.id,
            data_product.obj.id,
        )

    assert result == str(las_filepath)

    copc_filepath = data_product_dir / "upload.copc.laz"
    assert copc_filepath.exists()
    assert copc_filepath.stat().st_size > 0
    with laspy.open(str(copc_filepath)) as copc:
        assert copc.header.point_count == POINT_COUNT

    job_in_db = crud.job.get(db, id=data_product.job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.SUCCESS

    data_product_in_db = crud.data_product.get(db, id=data_product.obj.id)
    assert data_product_in_db is not None
    assert data_product_in_db.filepath == str(copc_filepath)
    assert data_product_in_db.is_initial_processing_completed

    # uploaded file must be removed from tusd storage after success
    assert not storage_path.exists()


def test_upload_point_cloud_repairs_invalid_header_bbox(
    db: Session, tmp_path: Path
) -> None:
    """A LAS with an unset header bounding box crashes untwine; the task must
    repair the header and still produce a valid, non-empty COPC.

    Regression test: this used to leave a 0-byte copc.laz while reporting
    SUCCESS because untwine's exit code was never checked.
    """
    data_product = SampleDataProduct(db, data_type="point_cloud")
    storage_path, las_filepath, data_product_dir = setup_upload_dirs(tmp_path)
    create_test_las(storage_path, zero_header_bbox=True)

    with patch("app.tasks.upload_tasks.get_db", side_effect=lambda: iter([db])):
        result = upload_point_cloud(
            str(storage_path),
            str(las_filepath),
            data_product.job.id,
            data_product.obj.id,
        )

    assert result == str(las_filepath)

    copc_filepath = data_product_dir / "upload.copc.laz"
    assert copc_filepath.exists()
    assert copc_filepath.stat().st_size > 0
    with laspy.open(str(copc_filepath)) as copc:
        assert copc.header.point_count == POINT_COUNT

    job_in_db = crud.job.get(db, id=data_product.job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.SUCCESS

    # temporary repaired copy must not be left behind
    assert not (las_filepath.parent / f"repaired_{las_filepath.name}").exists()


def test_upload_point_cloud_untwine_failure_marks_job_failed(
    db: Session, tmp_path: Path
) -> None:
    """When untwine and the repair retry both fail, the job must be marked
    FAILED and the data product directory removed."""
    data_product = SampleDataProduct(db, data_type="point_cloud")
    storage_path, las_filepath, data_product_dir = setup_upload_dirs(tmp_path)
    create_test_las(storage_path)
    original_filepath = data_product.obj.filepath

    crashed = subprocess.CompletedProcess(
        args=["untwine"], returncode=134, stdout="", stderr="assertion failed"
    )
    with (
        patch("app.tasks.upload_tasks.get_db", side_effect=lambda: iter([db])),
        patch("app.tasks.upload_tasks.subprocess.run", return_value=crashed),
    ):
        result = upload_point_cloud(
            str(storage_path),
            str(las_filepath),
            data_product.job.id,
            data_product.obj.id,
        )

    assert result is None

    job_in_db = crud.job.get(db, id=data_product.job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.FAILED

    # data product must not point at a COPC and its directory must be removed
    data_product_in_db = crud.data_product.get(db, id=data_product.obj.id)
    assert data_product_in_db is not None
    assert data_product_in_db.filepath == original_filepath
    assert not data_product_dir.exists()


def test_upload_point_cloud_empty_output_marks_job_failed(
    db: Session, tmp_path: Path
) -> None:
    """A clean untwine exit that leaves an empty COPC must fail the job
    instead of publishing a 0-byte file."""
    data_product = SampleDataProduct(db, data_type="point_cloud")
    storage_path, las_filepath, data_product_dir = setup_upload_dirs(tmp_path)
    create_test_las(storage_path)

    def fake_run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
        if cmd[0] == "untwine":
            # simulate untwine exiting cleanly but writing an empty file
            Path(cmd[cmd.index("-o") + 1]).touch()
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    with (
        patch("app.tasks.upload_tasks.get_db", side_effect=lambda: iter([db])),
        patch("app.tasks.upload_tasks.subprocess.run", side_effect=fake_run),
    ):
        result = upload_point_cloud(
            str(storage_path),
            str(las_filepath),
            data_product.job.id,
            data_product.obj.id,
        )

    assert result is None

    job_in_db = crud.job.get(db, id=data_product.job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.FAILED
    assert not data_product_dir.exists()


def test_upload_point_cloud_empty_copc_upload_marks_job_failed(
    db: Session, tmp_path: Path
) -> None:
    """An empty .copc.laz uploaded directly must never be published."""
    data_product = SampleDataProduct(db, data_type="point_cloud")
    storage_path, las_filepath, data_product_dir = setup_upload_dirs(
        tmp_path, filename="upload.copc.laz"
    )
    storage_path.touch()

    with patch("app.tasks.upload_tasks.get_db", side_effect=lambda: iter([db])):
        result = upload_point_cloud(
            str(storage_path),
            str(las_filepath),
            data_product.job.id,
            data_product.obj.id,
        )

    assert result is None

    job_in_db = crud.job.get(db, id=data_product.job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.FAILED
    assert not data_product_dir.exists()
