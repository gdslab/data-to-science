from datetime import date
from typing import Generator
from uuid import UUID

import logging
import pytest
from pystac.validation import validate
from sqlalchemy.orm import Session
from pystac_client import Client

from app import crud
from app.core.config import settings
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.flight import create_flight
from app.tests.utils.STACCollectionHelper import STACCollectionHelper
from app.utils.STACCollectionManager import STACCollectionManager
from app.utils.STACGenerator import STACGenerator, date_to_datetime


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


def test_remove_from_catalog(stac_collection_published: STACCollectionHelper) -> None:
    """Test removing a collection from the STAC catalog."""
    # Get collection ID from fixture
    collection_id = stac_collection_published.collection_id
    assert collection_id is not None

    # Create STAC Collection Manager
    scm = STACCollectionManager(collection_id=collection_id)

    # Verify collection exists before removal
    collection = scm.fetch_public_collection()
    assert collection is not None
    assert collection["id"] == collection_id

    # Remove collection from catalog
    scm.remove_from_catalog()

    # Verify collection no longer exists
    collection = scm.fetch_public_collection()
    assert collection is None


def test_remove_nonexistent_collection_from_catalog(db: Session) -> None:
    """Test attempting to remove a non-existent collection from the STAC catalog."""
    # Create STAC Collection Manager with non-existent collection ID
    collection_id = "00000000-0000-0000-0000-000000000000"  # Non-existent UUID
    scm = STACCollectionManager(collection_id=collection_id)

    # Verify collection doesn't exist
    collection = scm.fetch_public_collection()
    assert collection is None

    # Attempt to remove non-existent collection (should not raise an error)
    scm.remove_from_catalog()


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


def test_fetch_public_items(stac_collection_published: STACCollectionHelper) -> None:
    """Test fetching items from a published collection."""
    # Get collection ID from fixture
    collection_id = stac_collection_published.collection_id
    assert collection_id is not None

    # Create STAC Collection Manager
    scm = STACCollectionManager(collection_id=collection_id)

    # Fetch items
    items = scm.fetch_public_items()
    assert len(items) == 2  # We create 2 items in the fixture

    # Verify items exist
    for item_id in items:
        item = scm.fetch_public_item(item_id)
        assert item is not None
        assert item["id"] == item_id
        assert item["collection"] == collection_id


def test_fetch_public_item_nonexistent(
    stac_collection_published: STACCollectionHelper,
) -> None:
    """Test fetching a non-existent item."""
    # Get collection ID from fixture
    collection_id = stac_collection_published.collection_id
    assert collection_id is not None

    # Create STAC Collection Manager
    scm = STACCollectionManager(collection_id=collection_id)

    # Try to fetch non-existent item
    item = scm.fetch_public_item("nonexistent-item")
    assert item is None


def test_compare_and_update_no_changes(
    stac_collection_published: STACCollectionHelper,
) -> None:
    """Test compare_and_update when no changes are needed."""
    # Get collection and items from fixture
    collection_id = stac_collection_published.collection_id
    collection = stac_collection_published.collection
    items = stac_collection_published.items
    assert collection_id is not None
    assert collection is not None

    # Create STAC Collection Manager with same collection
    scm = STACCollectionManager(
        collection_id=collection_id, collection=collection, items=items
    )

    # Compare and update (should not make any changes)
    scm.compare_and_update()

    # Verify collection still exists and is unchanged
    public_collection = scm.fetch_public_collection()
    assert public_collection is not None
    assert public_collection["id"] == collection_id


def test_compare_and_update_with_changes(
    stac_collection_published: STACCollectionHelper,
) -> None:
    """Test compare_and_update when changes are needed."""
    # Get collection and items from fixture
    collection_id = stac_collection_published.collection_id
    collection = stac_collection_published.collection
    items = stac_collection_published.items
    assert collection_id is not None
    assert collection is not None

    # Modify the collection
    collection.title = "Updated Title"

    # Create STAC Collection Manager with modified collection
    scm = STACCollectionManager(
        collection_id=collection_id, collection=collection, items=items
    )

    # Compare and update (should update the collection)
    scm.compare_and_update()

    # Verify collection was updated
    public_collection = scm.fetch_public_collection()
    assert public_collection is not None
    assert public_collection["title"] == "Updated Title"


def test_compare_and_update_no_collection() -> None:
    """Test compare_and_update when no local collection is provided."""
    # Create STAC Collection Manager without a collection
    collection_id = "00000000-0000-0000-0000-000000000000"
    scm = STACCollectionManager(collection_id=collection_id)

    # Compare and update should raise ValueError
    with pytest.raises(ValueError, match="No local collection provided for comparison"):
        scm.compare_and_update()


def test_publish_to_catalog_no_collection() -> None:
    """Test publishing when no collection is provided."""
    # Create STAC Collection Manager without a collection
    collection_id = "00000000-0000-0000-0000-000000000000"
    scm = STACCollectionManager(collection_id=collection_id)

    # Publish should raise ValueError
    with pytest.raises(ValueError, match="No collection provided for publishing"):
        scm.publish_to_catalog()


def test_stac_generator_invalid_project(db: Session) -> None:
    """Test STACGenerator with an invalid project ID."""
    # Try to create STACGenerator with non-existent project
    project_id = UUID("00000000-0000-0000-0000-000000000000")
    with pytest.raises(ValueError, match="Project not found"):
        STACGenerator(db=db, project_id=project_id)


def test_stac_generator_no_flights(db: Session) -> None:
    """Test STACGenerator with a project that has no flights."""
    # Create project without flights
    project = create_project(db)

    # Try to create STACGenerator
    with pytest.raises(
        ValueError, match="Project must have at least one flight to publish"
    ):
        STACGenerator(db=db, project_id=project.id)


def test_stac_generator_no_data_products(db: Session) -> None:
    """Test STACGenerator with a project that has flights but no data products."""
    # Create project and flight but no data products
    project = create_project(db)
    create_flight(db, project_id=project.id)

    # Try to create STACGenerator
    with pytest.raises(ValueError, match="No data products found in project"):
        STACGenerator(db=db, project_id=project.id)


def test_stac_generator_temporal_extent_no_dates(db: Session) -> None:
    """Test STACGenerator's temporal extent when no dates are provided."""
    # Create project with flight but no planting/harvest dates
    project = create_project(db, no_dates=True)
    flight = create_flight(db, project_id=project.id)
    SampleDataProduct(db=db, flight=flight)

    # Create STACGenerator
    sg = STACGenerator(db=db, project_id=project.id)

    # Verify temporal extent uses flight dates
    temporal_extent = sg.collection.extent.temporal
    assert temporal_extent is not None

    # Since we only have one flight, both start and end dates should be the flight's acquisition date
    expected_date = date_to_datetime(flight.acquisition_date)
    assert temporal_extent.intervals[0][0] == expected_date
    assert temporal_extent.intervals[0][1] == expected_date


def test_stac_generator_temporal_extent_with_dates(db: Session) -> None:
    """Test STACGenerator's temporal extent when planting/harvest dates are provided."""
    # Create project with planting/harvest dates
    project = create_project(db)
    project_id = project.id  # Store ID before modifying

    # Update project dates
    project.planting_date = date(2024, 1, 1)
    project.harvest_date = date(2024, 12, 31)
    db.add(project)
    db.commit()

    # Add flight and data product
    flight = create_flight(db, project_id=project_id)
    SampleDataProduct(db=db, flight=flight)

    # Create STACGenerator
    sg = STACGenerator(db=db, project_id=project_id)

    # Verify temporal extent uses project dates
    temporal_extent = sg.collection.extent.temporal
    assert temporal_extent is not None

    # Get fresh project object to access dates
    project_in_db = crud.project.get(db, id=project_id)
    assert project_in_db is not None
    assert temporal_extent.intervals[0][0] == date_to_datetime(
        project_in_db.planting_date
    )
    assert temporal_extent.intervals[0][1] == date_to_datetime(
        project_in_db.harvest_date
    )
