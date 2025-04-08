from pystac.validation import validate
from sqlalchemy.orm import Session

from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.TestSTACCollection import TestSTACCollection
from app.utils.STACCollectionManager import STACCollectionManager
from app.utils.STACGenerator import STACGenerator


def test_fetch_public_metadata(db: Session) -> None:
    # Create STAC Collection on STAC API
    tsc = TestSTACCollection(db)
    tsc.create()
    collection_id = tsc.collection_id

    assert collection_id is not None

    # Fetch STAC Collection from STAC API
    scm = STACCollectionManager(collection_id=collection_id)
    collection = scm.fetch_public_collection()

    assert collection is not None
    assert collection["id"] == collection_id


def test_compare_and_update() -> None:
    pass


def test_publish_to_catalog() -> None:
    pass


def test_remove_from_catalog() -> None:
    pass


def test_is_stac_api_available() -> None:
    pass


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
