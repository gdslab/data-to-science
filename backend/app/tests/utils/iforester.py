import base64
import os
import shutil
from typing import Optional

from pydantic import UUID4
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.schemas.iforester import IForesterCreate, IForesterUpdate
from app.tests.utils.project import create_project

EXAMPLE_DATA = {
    "DBH": 0.8602302388288081136380469615687616169452667236328125,
    "depthImageFileName": "C1234567-89A0-1234-5678-901234567886.png",
    "distance": 5.38718104921281337738037109375,
    "RGB1XImageFileName": "C1234567-89A0-1234-5678-901234567886.jpg",
    "latitude": 40.9191434360109269618988037109375,
    "longitude": -86.574821412563323974609375,
    "note": "Nothing interesting",
    "phoneDirection": None,
    "phoneID": "C1234567-89A0-1234-5678-901234567890",
    "species": "Ash",
    "user": "VictorChen",
}

with open(
    os.path.join(os.sep, "app", "app", "tests", "data", "iforester_image.txt"), "r"
) as example_image_file:
    EXAMPLE_IMAGE = example_image_file.read()

with open(
    os.path.join(os.sep, "app", "app", "tests", "data", "iforester_png.txt"), "r"
) as example_png_file:
    EXAMPLE_PNG = example_png_file.read()


def create_iforester(db: Session, project_id: Optional[UUID4] = None):
    if not project_id:
        project = create_project(db)
        project_id = project.id
    iforester_in = IForesterCreate(**EXAMPLE_DATA)
    iforester_in.dbh = EXAMPLE_DATA["DBH"]
    iforester = crud.iforester.create_iforester(
        db, iforester_in=iforester_in, project_id=project_id
    )
    # write encoded images to static directory
    static_dir = os.path.join(
        settings.TEST_STATIC_DIR,
        "projects",
        str(project_id),
        "iforester",
        str(iforester.id),
    )
    os.makedirs(static_dir)
    image_in_bytes = str.encode(EXAMPLE_IMAGE)
    with open(
        os.path.join(static_dir, EXAMPLE_DATA["RGB1XImageFileName"]), "wb"
    ) as img_file:
        img_file.write(base64.decodebytes(image_in_bytes))
    png_in_bytes = str.encode(EXAMPLE_PNG)
    with open(
        os.path.join(static_dir, EXAMPLE_DATA["depthImageFileName"]), "wb"
    ) as png_file:
        png_file.write(base64.decodebytes(png_in_bytes))

    iforester_update_in = IForesterUpdate(
        imageFile=os.path.join(static_dir, EXAMPLE_DATA["RGB1XImageFileName"]),
        depthFile=os.path.join(static_dir, EXAMPLE_DATA["depthImageFileName"]),
    )
    crud.iforester.update(db, db_obj=iforester, obj_in=iforester_update_in)

    return iforester
