from typing import List, Optional

import logging
from pystac import Collection, Item
from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.flight import create_flight
from app.tests.utils.project import create_project
from app.utils.STACCollectionManager import STACCollectionManager
from app.utils.STACGenerator import STACGenerator


logger = logging.getLogger(__name__)


TEST_STAC_API_URL = "https://stac-dev.d2s.org"


class STACCollectionHelper:
    def __init__(self, db: Session):
        self.db = db

        # Set up project with two flights and two data products
        project = create_project(db)
        self.flight1 = create_flight(db, project_id=project.id)
        self.flight2 = create_flight(db, project_id=project.id)
        self.data_product1 = SampleDataProduct(db=db, flight=self.flight1).obj
        self.data_product2 = SampleDataProduct(
            db=db, flight=self.flight2, data_type="ortho"
        ).obj

        self.project_id = project.id
        self.collection_id: Optional[str] = None
        self.collection: Optional[Collection] = None
        self.items: Optional[List[Item]] = None

    def create(self, publish: bool = True) -> None:
        # Create STAC Collection using STACGenerator
        sg = STACGenerator(db=self.db, project_id=self.project_id)
        self.collection = sg.collection
        self.items = sg.items

        if self.collection:
            self.collection_id = self.collection.id

            # Create STAC Collection Manager with collection and items
            scm = STACCollectionManager(
                collection_id=self.collection_id,
                collection=self.collection,
                items=self.items,
            )

            # Publish collection to STAC API
            if publish:
                scm.publish_to_catalog()

                # Update the project to published and make all data products public
                # This mirrors what the real API endpoint does
                crud.project.update_project_visibility(
                    self.db, project_id=self.project_id, is_public=True
                )
        else:
            raise ValueError("Failed to create STAC collection")

    def destroy(self) -> None:
        if self.collection_id:
            try:
                # Create STAC Collection Manager to remove the collection
                scm = STACCollectionManager(collection_id=self.collection_id)
                scm.remove_from_catalog()
            except Exception as e:
                logger.error(
                    f"Failed to destroy STAC collection {self.collection_id}: {str(e)}"
                )
                # Re-raise to ensure test failure
                raise
