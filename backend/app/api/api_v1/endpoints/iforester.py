import base64
import os
from typing import Any, List

from fastapi import APIRouter, Depends, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()


def get_iforester_static_dir(project_id: UUID4, iforester_id: UUID4):
    """Get directory where iforester images are stored.

    Args:
        project_id (UUID4): Project ID associated with iforester files.
        iforester_id (UUID4): IForester ID associated with iforester db record.

    Returns:
        str: Path to iforester static directory.
    """
    if os.environ.get("RUNNING_TESTS") == "1":
        iforester_static_dir = (
            f"{settings.TEST_STATIC_DIR}/projects/{project_id}/iforester/{iforester_id}"
        )
    else:
        iforester_static_dir = (
            f"{settings.STATIC_DIR}/projects/{project_id}/iforester/{iforester_id}"
        )

    # create folder if it does not exist
    if not os.path.exists(iforester_static_dir):
        os.makedirs(iforester_static_dir)

    return iforester_static_dir


@router.post("", response_model=schemas.IForester, status_code=status.HTTP_201_CREATED)
def create_iforester(
    iforester_in: schemas.IForesterPost,
    project: models.Project = Depends(deps.can_read_write_project_with_jwt_or_api_key),
    db: Session = Depends(deps.get_db),
) -> Any:
    iforester_dict = iforester_in.model_dump()
    iforester_dict["dbh"] = iforester_dict.get("DBH")
    if "DBH" in iforester_dict:
        del iforester_dict["DBH"]
    iforester_in_db = schemas.IForesterCreate(**iforester_dict)
    iforester = crud.iforester.create_iforester(
        db, iforester_in=iforester_in_db, project_id=project.id
    )
    # decode and write images to disk
    static_dir = get_iforester_static_dir(project.id, iforester.id)
    # rgb1x image
    if iforester_in.image and iforester_in.RGB1XImageFileName:
        img_file_in_bytes = str.encode(iforester_in.image)
        with open(
            os.path.join(static_dir, iforester_in.RGB1XImageFileName), "wb"
        ) as img_file:
            img_file.write(base64.decodebytes(img_file_in_bytes))
    # depth image
    if iforester_in.png and iforester_in.depthImageFileName:
        img_file_in_bytes = str.encode(iforester_in.png)
        with open(
            os.path.join(static_dir, iforester_in.depthImageFileName), "wb"
        ) as img_file:
            img_file.write(base64.decodebytes(img_file_in_bytes))

    # add images to newly created record
    if iforester_in.RGB1XImageFileName and iforester_in.depthImageFileName:
        iforester_update_in = schemas.IForesterUpdate(
            imageFile=os.path.join(static_dir, iforester_in.RGB1XImageFileName),
            depthFile=os.path.join(static_dir, iforester_in.depthImageFileName),
        )
        iforester = crud.iforester.update(
            db, db_obj=iforester, obj_in=iforester_update_in
        )

    return iforester


@router.get("/{iforester_id}", response_model=schemas.IForester)
def read_iforester(
    iforester_id: UUID4,
    project: models.Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    iforester = crud.iforester.get_iforester_by_id(
        db, iforester_id=iforester_id, project_id=project.id
    )
    return iforester


@router.get("", response_model=List[schemas.IForester])
def read_multi_iforester(
    project: models.Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    iforesters = crud.iforester.get_multi_iforester_by_project_id(
        db, project_id=project.id
    )
    return iforesters


@router.put("/{iforester_id}", response_model=schemas.IForester)
def update_iforester(
    iforester_id: UUID4,
    iforester_in: schemas.IForesterUpdate,
    project: models.Project = Depends(deps.can_read_write_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    iforester = crud.iforester.update_iforester_by_id(
        db, iforester_in=iforester_in, iforester_id=iforester_id, project_id=project.id
    )
    return iforester


@router.delete(
    "/{iforester_id}", response_model=schemas.IForester, status_code=status.HTTP_200_OK
)
def delete_iforester(
    iforester_id: UUID4,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    iforester = crud.iforester.remove_iforester_by_id(
        db, iforester_id=iforester_id, project_id=project.id
    )
    return iforester
