from typing import Optional

from pydantic import UUID4
from sqlalchemy.orm import Session

from app import crud
from app.schemas.iforester import IForesterCreate
from app.tests.utils.project import create_project

EXAMPLE_DATA = {
    "dbh": 0.8602302388288081136380469615687616169452667236328125,
    "depthFile": "C1234567-89A0-1234-5678-901234567886.png",
    "distance": 5.38718104921281337738037109375,
    "imageFile": "C1234567-89A0-1234-5678-901234567886.jpg",
    "latitude": 40.9191434360109269618988037109375,
    "longitude": -86.574821412563323974609375,
    "note": "Nothing interesting",
    "phoneDirection": None,
    "phoneID": "C1234567-89A0-1234-5678-901234567890",
    "species": "Ash",
    "user": "VictorChen",
}


def create_iforester(db: Session, project_id: Optional[UUID4] = None):
    if not project_id:
        project = create_project(db)
        project_id = project.id
    iforester_in = IForesterCreate(**EXAMPLE_DATA)
    return crud.iforester.create_iforester(
        db, iforester_in=iforester_in, project_id=project_id
    )
