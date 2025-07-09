from datetime import date
from typing import Generator
from uuid import UUID

import pytest
from pystac.validation import validate
from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.flight import create_flight
from app.tests.utils.STACCollectionHelper import STACCollectionHelper

from app.utils.STACCollectionManager import STACCollectionManager
from app.utils.STACGenerator import STACGenerator, date_to_datetime


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

    # Create flight with a name and data product
    flight_with_name = create_flight(db, project_id=project.id, name="Test Flight Name")
    data_product_with_name = SampleDataProduct(
        db, project=project, flight=flight_with_name
    )

    # Create flight without a name and data product
    flight_without_name = create_flight(db, project_id=project.id, name=None)
    data_product_without_name = SampleDataProduct(
        db, project=project, flight=flight_without_name
    )

    # Generate STAC Items
    sg = STACGenerator(db, project_id=project.id)

    # Get STAC generated STAC items
    stac_items = sg.items

    # Get STAC generated STAC collection
    stac_collection = sg.collection

    # Assert that both STAC items were created
    assert len(stac_items) == 2

    # Validate STAC Items and Collection
    for item in stac_items:
        assert validate(item)
    assert validate(stac_collection)

    # Test flight_name handling for each item
    for item in stac_items:
        flight_details = item.properties["flight_details"]

        if item.id == str(data_product_with_name.obj.id):
            # Flight with name should include flight_name
            assert "flight_name" in flight_details
            assert flight_details["flight_name"] == "Test Flight Name"
            assert flight_details["flight_id"] == str(flight_with_name.id)
        elif item.id == str(data_product_without_name.obj.id):
            # Flight without name should NOT include flight_name
            assert "flight_name" not in flight_details
            assert flight_details["flight_id"] == str(flight_without_name.id)

        # Verify other expected fields are present in both cases
        assert "acquisition_date" in flight_details
        assert "platform" in flight_details
        assert "sensor" in flight_details


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
        ValueError,
        match="Project must have at least one flight with a data product to publish",
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


def test_fetch_public_items_full(
    stac_collection_published: STACCollectionHelper,
) -> None:
    """Test fetching full item dictionaries from a published collection."""
    # Get collection ID from fixture
    collection_id = stac_collection_published.collection_id
    assert collection_id is not None

    # Create STAC Collection Manager
    scm = STACCollectionManager(collection_id=collection_id)

    # Fetch full items
    items = scm.fetch_public_items_full()
    assert len(items) == 2  # We create 2 items in the fixture

    # Verify items are full dictionaries with expected structure
    for item in items:
        assert isinstance(item, dict)
        assert "id" in item
        assert "type" in item
        assert "collection" in item
        assert "properties" in item
        assert "geometry" in item
        assert "bbox" in item
        assert item["collection"] == collection_id
        assert item["type"] == "Feature"

        # Verify flight details are present
        assert "flight_details" in item["properties"]
        assert "data_product_details" in item["properties"]


def test_fetch_public_items_full_empty_collection() -> None:
    """Test fetching full items from a non-existent collection returns empty list."""
    # Create STAC Collection Manager with non-existent collection ID
    collection_id = "00000000-0000-0000-0000-000000000000"
    scm = STACCollectionManager(collection_id=collection_id)

    # Fetch full items should return empty list
    items = scm.fetch_public_items_full()
    assert isinstance(items, list)
    assert len(items) == 0


def test_stac_generator_with_scientific_metadata(db: Session) -> None:
    """Test STACGenerator with scientific DOI and citation."""
    # Create new project
    project = create_project(db)

    # Add sample data product to project
    data_product = SampleDataProduct(db, project=project)

    # Get flight from data product
    flight = data_product.flight

    # Scientific metadata
    test_doi = "10.1000/stac123"
    test_citation = (
        "STAC, Test, et al. (2023). STAC Test Dataset. STAC Journal, 1(1), 1-10."
    )

    # Generate STAC with scientific metadata
    sg = STACGenerator(
        db, project_id=project.id, sci_doi=test_doi, sci_citation=test_citation
    )

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

    # Verify scientific extension and metadata are present
    collection_dict = stac_collection.to_dict()
    assert "stac_extensions" in collection_dict
    assert (
        "https://stac-extensions.github.io/scientific/v1.0.0/schema.json"
        in collection_dict["stac_extensions"]
    )
    assert collection_dict.get("sci:doi") == test_doi
    assert collection_dict.get("sci:citation") == test_citation


def test_stac_generator_with_only_doi(db: Session) -> None:
    """Test STACGenerator with only DOI (no citation)."""
    # Create new project
    project = create_project(db)

    # Add sample data product to project
    data_product = SampleDataProduct(db, project=project)

    # Only DOI, no citation
    test_doi = "10.1000/stac456"

    # Generate STAC with only DOI
    sg = STACGenerator(db, project_id=project.id, sci_doi=test_doi)

    # Get STAC generated STAC collection
    stac_collection = sg.collection

    # Validate STAC Collection
    assert validate(stac_collection)

    # Verify scientific extension and DOI are present, but no citation
    collection_dict = stac_collection.to_dict()
    assert "stac_extensions" in collection_dict
    assert (
        "https://stac-extensions.github.io/scientific/v1.0.0/schema.json"
        in collection_dict["stac_extensions"]
    )
    assert collection_dict.get("sci:doi") == test_doi
    assert "sci:citation" not in collection_dict


def test_stac_generator_with_only_citation(db: Session) -> None:
    """Test STACGenerator with only citation (no DOI)."""
    # Create new project
    project = create_project(db)

    # Add sample data product to project
    data_product = SampleDataProduct(db, project=project)

    # Only citation, no DOI
    test_citation = "Citation, Only, et al. (2023). Citation Only Dataset. Citation Journal, 2(1), 5-15."

    # Generate STAC with only citation
    sg = STACGenerator(db, project_id=project.id, sci_citation=test_citation)

    # Get STAC generated STAC collection
    stac_collection = sg.collection

    # Validate STAC Collection
    assert validate(stac_collection)

    # Verify scientific extension and citation are present, but no DOI
    collection_dict = stac_collection.to_dict()
    assert "stac_extensions" in collection_dict
    assert (
        "https://stac-extensions.github.io/scientific/v1.0.0/schema.json"
        in collection_dict["stac_extensions"]
    )
    assert collection_dict.get("sci:citation") == test_citation
    assert "sci:doi" not in collection_dict


def test_stac_generator_without_scientific_metadata(db: Session) -> None:
    """Test STACGenerator without scientific metadata (ensures backward compatibility)."""
    # Create new project
    project = create_project(db)

    # Add sample data product to project
    data_product = SampleDataProduct(db, project=project)

    # Get flight from data product
    flight = data_product.flight

    # Generate STAC without scientific metadata
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

    # Verify scientific extension and metadata are NOT present
    collection_dict = stac_collection.to_dict()
    if "stac_extensions" in collection_dict:
        assert (
            "https://stac-extensions.github.io/scientific/v1.0.0/schema.json"
            not in collection_dict["stac_extensions"]
        )
    assert "sci:doi" not in collection_dict
    assert "sci:citation" not in collection_dict


def test_stac_generator_with_custom_titles(db: Session) -> None:
    """Test STACGenerator with custom titles for STAC items."""
    # Create new project
    project = create_project(db)

    # Add sample data products to project
    data_product1 = SampleDataProduct(db, project=project)
    data_product2 = SampleDataProduct(db, project=project)

    # Custom titles for the data products
    custom_titles = {
        str(data_product1.obj.id): "Custom Title for Item 1",
        str(data_product2.obj.id): "Custom Title for Item 2",
    }

    # Generate STAC with custom titles
    sg = STACGenerator(db, project_id=project.id, custom_titles=custom_titles)

    # Get STAC generated STAC items
    stac_items = sg.items

    # Get STAC generated STAC collection
    stac_collection = sg.collection

    # Assert that the STAC items were created
    assert len(stac_items) == 2

    # Validate STAC Items
    for item in stac_items:
        assert validate(item)

    # Validate STAC Collection
    assert validate(stac_collection)

    # Verify custom titles are used
    for item in stac_items:
        item_id = item.id
        if item_id == str(data_product1.obj.id):
            assert item.properties["title"] == "Custom Title for Item 1"
        elif item_id == str(data_product2.obj.id):
            assert item.properties["title"] == "Custom Title for Item 2"


def test_stac_generator_with_partial_custom_titles(db: Session) -> None:
    """Test STACGenerator with custom titles for only some STAC items."""
    # Create new project
    project = create_project(db)

    # Add sample data products to project
    data_product1 = SampleDataProduct(db, project=project)
    data_product2 = SampleDataProduct(db, project=project)

    # Custom title for only one data product
    custom_titles = {
        str(data_product1.obj.id): "Custom Title for Item 1",
        # data_product2 will use default title
    }

    # Generate STAC with partial custom titles
    sg = STACGenerator(db, project_id=project.id, custom_titles=custom_titles)

    # Get STAC generated STAC items
    stac_items = sg.items

    # Assert that the STAC items were created
    assert len(stac_items) == 2

    # Verify titles
    for item in stac_items:
        item_id = item.id
        if item_id == str(data_product1.obj.id):
            assert item.properties["title"] == "Custom Title for Item 1"
        elif item_id == str(data_product2.obj.id):
            # Should use default title format
            flight = data_product2.flight
            expected_title = f"{flight.acquisition_date}_{data_product2.obj.data_type}_{flight.sensor}_{flight.platform}"
            assert item.properties["title"] == expected_title


def test_stac_generator_with_empty_custom_titles(db: Session) -> None:
    """Test STACGenerator with empty custom titles (should use defaults)."""
    # Create new project
    project = create_project(db)

    # Add sample data product to project
    data_product = SampleDataProduct(db, project=project)

    # Get flight from data product
    flight = data_product.flight

    # Custom titles with empty string (should use default)
    custom_titles = {
        str(data_product.obj.id): "",
    }

    # Generate STAC with empty custom titles
    sg = STACGenerator(db, project_id=project.id, custom_titles=custom_titles)

    # Get STAC generated STAC items
    stac_items = sg.items

    # Assert that the STAC item was created
    assert len(stac_items) == 1
    assert stac_items[0].id == str(data_product.obj.id)

    # Verify default title is used when custom title is empty
    expected_title = f"{flight.acquisition_date}_{data_product.obj.data_type}_{flight.sensor}_{flight.platform}"
    assert stac_items[0].properties["title"] == expected_title


def test_publish_to_catalog_with_scientific_metadata(db: Session) -> None:
    """Test publishing a collection with scientific metadata to the catalog."""
    # Create new project
    project = create_project(db)

    # Add sample data product to project
    data_product = SampleDataProduct(db, project=project)

    # Scientific metadata
    test_doi = "10.1000/publish123"
    test_citation = "Publish, Test, et al. (2023). Published Dataset. Publishing Journal, 3(1), 10-20."

    # Generate STAC with scientific metadata using STACGenerator
    sg = STACGenerator(
        db, project_id=project.id, sci_doi=test_doi, sci_citation=test_citation
    )
    stac_collection = sg.collection
    stac_items = sg.items

    # Create STAC Collection Manager
    scm = STACCollectionManager(
        collection_id=stac_collection.id,
        collection=stac_collection,
        items=stac_items,
    )

    # Publish STAC Collection to STAC API
    stac_report = scm.publish_to_catalog()
    assert stac_report.is_published is True

    # Fetch published STAC Collection from STAC API
    public_collection = scm.fetch_public_collection()

    assert public_collection is not None
    assert public_collection["id"] == stac_collection.id

    # Verify scientific extension and metadata are present in published collection
    assert "stac_extensions" in public_collection
    assert (
        "https://stac-extensions.github.io/scientific/v1.0.0/schema.json"
        in public_collection["stac_extensions"]
    )
    assert public_collection.get("sci:doi") == test_doi
    assert public_collection.get("sci:citation") == test_citation

    # Clean up - remove the published collection
    scm.remove_from_catalog()


def test_stac_generator_with_custom_license(db: Session) -> None:
    """Test STACGenerator with custom license."""
    # Create new project
    project = create_project(db)

    # Add sample data product to project
    data_product = SampleDataProduct(db, project=project)

    # Get flight from data product
    flight = data_product.flight

    # Test with custom license
    custom_license = "MIT"

    # Generate STAC with custom license
    sg = STACGenerator(db, project_id=project.id, license=custom_license)

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

    # Confirm license is set correctly
    collection_dict = stac_collection.to_dict()
    assert collection_dict["license"] == custom_license

    # Confirm flight id is present in STAC Item
    assert stac_items[0].properties["flight_details"]["flight_id"] == str(flight.id)


def test_stac_generator_with_default_license(db: Session) -> None:
    """Test STACGenerator uses default license when none provided."""
    # Create new project
    project = create_project(db)

    # Add sample data product to project
    data_product = SampleDataProduct(db, project=project)

    # Generate STAC without specifying license (should use default)
    sg = STACGenerator(db, project_id=project.id)

    # Get STAC generated STAC collection
    stac_collection = sg.collection

    # Validate STAC Collection
    assert validate(stac_collection)

    # Confirm default license is set
    collection_dict = stac_collection.to_dict()
    assert collection_dict["license"] == "CC-BY-NC-4.0"


def test_publish_to_catalog_with_custom_license(db: Session) -> None:
    """Test publishing a collection with custom license to the catalog."""
    # Create new project
    project = create_project(db)

    # Add sample data product to project
    data_product = SampleDataProduct(db, project=project)

    # Test with ISC license
    test_license = "ISC"

    # Generate STAC with custom license using STACGenerator
    sg = STACGenerator(db, project_id=project.id, license=test_license)
    stac_collection = sg.collection
    stac_items = sg.items

    # Create STAC Collection Manager
    scm = STACCollectionManager(
        collection_id=stac_collection.id,
        collection=stac_collection,
        items=stac_items,
    )

    # Publish STAC Collection to STAC API
    stac_report = scm.publish_to_catalog()
    assert stac_report.is_published is True

    # Fetch published STAC Collection from STAC API
    public_collection = scm.fetch_public_collection()

    assert public_collection is not None
    assert public_collection["id"] == stac_collection.id

    # Verify license is present in published collection
    assert public_collection.get("license") == test_license

    # Clean up - remove the published collection
    scm.remove_from_catalog()
