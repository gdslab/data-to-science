import logging
import os

from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models.extension import Extension

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load() -> None:
    db = SessionLocal()
    extensions = os.environ.get("EXTENSIONS")
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


def main() -> None:
    logger.info("Loading extensions")
    load()
    logger.info("Extension loaded")


if __name__ == "__main__":
    main()
