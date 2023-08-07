from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from app import models
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def upload_raw_data(
    file: UploadFile,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
):
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    # write uploaded file to disk in 1 MB chunks
    file_ext = Path(file.filename).suffix
    with open(f"{settings.UPLOAD_DIR}/{str(uuid4())}{file_ext}", "wb") as f:
        chunk_size = 1024 * 1024
        chunk = file.file_read(chunk_size)
        while chunk:
            f.write(chunk)
            chunk = file.file_read(chunk_size)
    return status.HTTP_201_CREATED
