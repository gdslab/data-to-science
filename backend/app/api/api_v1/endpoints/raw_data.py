import os
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.core.config import settings

from app.utils.ImageProcessor import ImageProcessor

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def upload_raw_data(
    files: UploadFile,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
):
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    upload_dir = f"{settings.UPLOAD_DIR}/{project.id}"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    out_path = os.path.join(upload_dir, f"{str(uuid4())}__temp.tif")

    with open(out_path, "wb") as buffer:
        shutil.copyfileobj(files.file, buffer)
        # create COG for uploaded GeoTIFF if necessary
        ip = ImageProcessor(out_path)
        cog_path = ip.run()

    return status.HTTP_201_CREATED
