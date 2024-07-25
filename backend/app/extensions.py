import logging
import os
from typing import List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.db.base import *
from app.db.session import SessionLocal
from app.models.extension import Extension

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_extensions_in_db(db: Session) -> List[Extension]:
    extensions = crud.extension.get_extensions(db)
    return extensions


def load() -> None:
    db = SessionLocal()
    extensions_in_db = get_extensions_in_db(db)
    extensions = os.environ.get("EXTENSIONS")
    if extensions and isinstance(extensions, str):
        for extension in extensions.split(","):
            extension_obj = Extension(name=extension)
            try:
                with db as session:
                    session.add(extension_obj)
                    session.commit()
                    session.refresh(extension_obj)
            except IntegrityError as e:
                # ignore - extension already in db
                logger.warning(f"Extension '{extension}' already in db")
            except Exception as e:
                logger.error(e)
                raise e
    # remove any extensions in database that are no longer in EXTENSIONS env var
    for extension in extensions_in_db:
        if extensions and isinstance(extensions, str):
            if extension.name not in extensions.split(","):
                try:
                    crud.extension.remove(db, id=extension.id)
                except Exception as e:
                    logger.error(e)
                    raise e
        else:
            try:
                crud.extension.remove(db, id=extension.id)
            except Exception as e:
                logger.error(e)
                raise e


def main() -> None:
    logger.info("Loading extensions")
    load()
    logger.info("Extension loaded")


if __name__ == "__main__":
    main()
