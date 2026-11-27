from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.flight import create_flight
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user
from app.utils.tusd.post_processing import process_data_product_uploaded_to_tusd


def _process(db: Session, tmp_path: Path, filename: str) -> dict:
    user = create_user(db)
    project = create_project(db, owner_id=user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=user.id)
    storage_path = tmp_path / "upload"
    storage_path.write_bytes(b"fake geotiff bytes")
    return process_data_product_uploaded_to_tusd(
        db,
        user_id=user.id,
        storage_path=storage_path,
        original_filename=Path(filename),
        dtype="ortho",
        project_id=project.id,
        flight_id=flight.id,
    )


@pytest.mark.parametrize("filename", ["ortho.tiff", "ORTHO.TIFF"])
def test_tiff_upload_is_stored_as_tif(
    db: Session, tmp_path: Path, filename: str
) -> None:
    with patch(
        "app.utils.tusd.post_processing.upload_geotiff.apply_async"
    ) as mock_apply:
        result = _process(db, tmp_path, filename)

    assert result["status"] == "processing"
    mock_apply.assert_called_once()
    destination_filepath = mock_apply.call_args.kwargs["args"][1]
    assert destination_filepath.endswith(".tif")
    data_product = crud.data_product.get(db, id=UUID(result["data_product_id"]))
    assert data_product is not None
    assert data_product.original_filename == filename


def test_unsupported_extension_is_rejected(db: Session, tmp_path: Path) -> None:
    with patch(
        "app.utils.tusd.post_processing.upload_geotiff.apply_async"
    ) as mock_apply:
        with pytest.raises(HTTPException) as exc_info:
            _process(db, tmp_path, "ortho.txt")

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    mock_apply.assert_not_called()
