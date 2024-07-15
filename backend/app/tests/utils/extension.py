from sqlalchemy.orm import Session

from app import crud
from app.schemas.extension import ExtensionCreate


def create_extension(
    db: Session, name: str = "ext1", description: str = "Extension 1"
) -> None:
    extension_in = ExtensionCreate(description=description, name=name)
    extension = crud.extension.create_extension(db, extension_in=extension_in)
    return extension
