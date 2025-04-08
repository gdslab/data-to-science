import requests
from typing import List, Optional

from pystac import Collection, Item
from sqlalchemy.orm import Session

from app.tests.utils.data_product import SampleDataProduct
from app.utils.STACCollectionManager import STACCollectionManager
from app.utils.STACGenerator import STACGenerator


TEST_STAC_API_URL = "https://stac-dev.d2s.org"


class TestSTACCollection:
    def __init__(self, db: Session):
        self.db = db
        self.data_product = SampleDataProduct(db=db)
        self.project = self.data_product.project

        self.collection_id: Optional[str] = None
        self.collection: Optional[Collection] = None
        self.items: Optional[List[Item]] = None

    def create(self) -> None:
        # Create STAC Collection using STACGenerator
        sg = STACGenerator(db=self.db, project_id=self.project.id)
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
            scm.publish_to_catalog()
        else:
            raise ValueError("Failed to create STAC collection")

    def destroy(self) -> None:
        if self.collection_id:
            # Create STAC Collection Manager to remove the collection
            scm = STACCollectionManager(collection_id=self.collection_id)
            scm.remove_from_catalog()
