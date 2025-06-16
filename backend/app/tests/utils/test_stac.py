from typing import Generator

import logging
import pytest
from pystac.validation import validate
from sqlalchemy.orm import Session
from pystac_client import Client

from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.STACCollectionHelper import STACCollectionHelper
from app.utils.STACCollectionManager import STACCollectionManager
from app.utils.STACGenerator import STACGenerator
from app.core.config import settings


logger = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
def cleanup_stac_catalog():
    """Fixture to clean up any collections from the test STAC catalog after all tests run."""
    yield  # Let all tests run first

    try:
        # Connect to STAC API
        stac_url = settings.get_stac_api_url
        if not stac_url:
            return

        client = Client.open(str(stac_url))
        collections = client.get_collections()

        # Remove all collections since this is a test-only catalog
        for collection in collections:
            collection_id = collection.id
            if collection_id:
                try:
                    logger.info(f"Cleaning up collection {collection_id}")
                    scm = STACCollectionManager(collection_id=collection_id)
                    scm.remove_from_catalog()
                except Exception as e:
                    logger.error(
                        f"Failed to cleanup collection {collection_id}: {str(e)}"
                    )
    except Exception as e:
        logger.error(f"Failed to cleanup STAC catalog: {str(e)}")


@pytest.fixture
def stac_collection_published(
    db: Session,
) -> Generator[STACCollectionHelper, None, None]:
    # Setup
    tsc = STACCollectionHelper(db)
    tsc.create(publish=True)

    # Yield the collection for use in the test
    yield tsc

    # Teardown (runs after the test, even if it fails)
    tsc.destroy()


@pytest.fixture
def stac_collection_unpublished(
    db: Session,
) -> Generator[STACCollectionHelper, None, None]:
    # Setup
    tsc = STACCollectionHelper(db)
    tsc.create(publish=False)

    # Yield the collection for use in the test
    yield tsc

    # Teardown (runs after the test, even if it fails)
    tsc.destroy()


def test_fetch_public_metadata(db: Session) -> None:
    # Create STAC Collection on STAC API
    tsc = STACCollectionHelper(db)
    tsc.create()
    collection_id = tsc.collection_id

    assert collection_id is not None

    # Fetch STAC Collection from STAC API
    scm = STACCollectionManager(collection_id=collection_id)
    collection = scm.fetch_public_collection()

    assert collection is not None
    assert collection["id"] == collection_id


def test_fetch_public_metadata_with_invalid_collection_id(db: Session) -> None:
    collection_id = "invalid_collection_id"

    # Fetch STAC Collection from STAC API
    scm = STACCollectionManager(collection_id=collection_id)
    collection = scm.fetch_public_collection()

    assert collection is None


def test_publish_to_catalog(stac_collection_unpublished: STACCollectionHelper) -> None:
    # Generate STAC Collection with two items
    tsc = stac_collection_unpublished

    # Get STAC Collection ID
    stac_collection_id = tsc.collection_id
    assert stac_collection_id is not None

    # Get STAC generated STAC collection
    stac_collection = tsc.collection
    assert stac_collection is not None

    # Get STAC generated STAC items
    stac_items = tsc.items
    assert stac_items is not None

    # Create STAC Collection Manager
    scm = STACCollectionManager(
        collection_id=stac_collection.id,
        collection=stac_collection,
        items=stac_items,
    )

    # Publish STAC Collection to STAC API
    scm.publish_to_catalog()

    # Fetch published STAC Collection from STAC API
    public_collection = scm.fetch_public_collection()

    assert public_collection is not None
    assert public_collection["id"] == stac_collection.id

    # Fetch list of published STAC Items from STAC API
    public_items = scm.fetch_public_items()

    assert public_items is not None
    assert len(public_items) == len(stac_items)

    # Assert that the STAC items are the same
    for stac_item in stac_items:
        assert stac_item.id in public_items

    # Fetch published STAC Item from STAC API
    public_item = scm.fetch_public_item(str(tsc.data_product1.id))

    assert public_item is not None
    assert public_item["id"] == str(tsc.data_product1.id)

    # Confirm correct flight id is present in STAC Item
    assert public_item["properties"]["flight_details"]["flight_id"] == str(
        tsc.flight1.id
    )

    # Fetch published STAC Item from STAC API
    public_item = scm.fetch_public_item(str(tsc.data_product2.id))

    assert public_item is not None
    assert public_item["id"] == str(tsc.data_product2.id)

    # Confirm correct flight id is present in STAC Item
    assert public_item["properties"]["flight_details"]["flight_id"] == str(
        tsc.flight2.id
    )


def test_is_stac_api_available(stac_collection_published: STACCollectionHelper) -> None:
    stac_collection_id = stac_collection_published.collection_id
    assert stac_collection_id is not None

    scm = STACCollectionManager(collection_id=stac_collection_id)
    assert scm.is_stac_api_available()


def test_stac_generator(db: Session) -> None:
    # Create new project
    project = create_project(db)

    # Add sample data product to project
    data_product = SampleDataProduct(db, project=project)

    # Get flight from data product
    flight = data_product.flight

    # Generate STAC Item
    sg = STACGenerator(db, project_id=project.id)

    # Get STAC generated STAC items
    stac_items = sg.items

    # Get STAC generated STAC collection
    stac_collection = sg.collection

    # Assert that the STAC item was created
    assert len(stac_items) == 1
    assert stac_items[0].id == str(data_product.obj.id)

    # Validate STAC Item
    assert validate(stac_items[0])

    # Validate STAC Collection
    assert validate(stac_collection)

    # Confirm flight id is present in STAC Item
    assert stac_items[0].properties["flight_details"]["flight_id"] == str(flight.id)
