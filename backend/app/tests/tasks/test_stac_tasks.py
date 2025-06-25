import json
import pytest
import tempfile
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch, MagicMock

from sqlalchemy.orm import Session

from app.tasks.stac_tasks import (
    generate_stac_preview_task,
    publish_stac_catalog_task,
    get_stac_cache_path,
    UUIDEncoder,
)
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project import create_project
from app.tests.utils.flight import create_flight

from app.core.config import settings


def test_get_stac_cache_path():
    """Test the get_stac_cache_path helper function."""
    project_id = uuid4()

    # Mock the settings to use TEST_STATIC_DIR in tests
    with patch.object(settings, "STATIC_DIR", settings.TEST_STATIC_DIR):
        cache_path = get_stac_cache_path(project_id)

        # Verify path structure
        expected_path = (
            Path(settings.TEST_STATIC_DIR) / "projects" / str(project_id) / "stac.json"
        )
        assert cache_path == expected_path
        assert cache_path.suffix == ".json"


def test_uuid_encoder():
    """Test the UUIDEncoder class."""
    test_uuid = uuid4()
    test_data = {
        "id": test_uuid,
        "name": "test",
        "number": 123,
    }

    # Should be able to serialize UUID
    json_str = json.dumps(test_data, cls=UUIDEncoder)
    assert str(test_uuid) in json_str

    # Should be able to deserialize back
    deserialized = json.loads(json_str)
    assert deserialized["id"] == str(test_uuid)
    assert deserialized["name"] == "test"
    assert deserialized["number"] == 123


def test_uuid_encoder_with_datetime():
    """Test the UUIDEncoder class with datetime objects."""
    from datetime import datetime

    test_datetime = datetime(2023, 12, 25, 12, 0, 0)
    test_data = {
        "timestamp": test_datetime,
        "name": "test",
    }

    # Should be able to serialize datetime
    json_str = json.dumps(test_data, cls=UUIDEncoder)
    assert "2023-12-25T12:00:00" in json_str

    # Should be able to deserialize back
    deserialized = json.loads(json_str)
    assert deserialized["timestamp"] == "2023-12-25T12:00:00"
    assert deserialized["name"] == "test"


@patch("app.tasks.stac_tasks.get_db")
def test_generate_stac_preview_task_success(mock_get_db, db: Session):
    """Test successful STAC preview generation task."""
    # Setup
    mock_get_db.return_value.__enter__.return_value = db

    # Create project with data
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock settings to use temp directory
        with patch.object(settings, "STATIC_DIR", temp_dir):
            # Call the task
            result = generate_stac_preview_task(str(project.id), db=db)

            # Verify result structure (STAC data, not status response)
            assert "collection_id" in result
            assert str(result["collection_id"]) == str(project.id)
            assert "collection" in result
            assert "items" in result
            assert result["is_published"] is False
            assert len(result["items"]) == 1

            # Verify cache file was created
            cache_path = get_stac_cache_path(project.id)
            assert cache_path.exists()

            # Verify cache content
            with open(cache_path, "r") as f:
                cached_data = json.load(f)
            assert str(cached_data["collection_id"]) == str(project.id)
            assert cached_data["is_published"] is False
            assert len(cached_data["items"]) == 1


@patch("app.tasks.stac_tasks.get_db")
def test_generate_stac_preview_task_with_parameters(mock_get_db, db: Session):
    """Test STAC preview generation task with scientific metadata and custom titles."""
    # Setup
    mock_get_db.return_value.__enter__.return_value = db

    # Create project with data
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Parameters
    sci_doi = "10.1000/test123"
    sci_citation = (
        "Test, Author, et al. (2023). Test Dataset. Test Journal, 1(1), 1-10."
    )
    custom_titles = {str(data_product.obj.id): "Custom Test Title"}

    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock settings to use temp directory
        with patch.object(settings, "STATIC_DIR", temp_dir):
            # Call the task
            result = generate_stac_preview_task(
                str(project.id),
                sci_doi=sci_doi,
                sci_citation=sci_citation,
                custom_titles=custom_titles,
                db=db,
            )

            # Verify result structure
            assert "collection_id" in result
            assert str(result["collection_id"]) == str(project.id)
            assert result["is_published"] is False

            # Verify cache file was created with parameters
            cache_path = get_stac_cache_path(project.id)
            assert cache_path.exists()

            # Verify cache content includes scientific metadata
            with open(cache_path, "r") as f:
                cached_data = json.load(f)
            assert cached_data["collection"]["sci:doi"] == sci_doi
            assert cached_data["collection"]["sci:citation"] == sci_citation

            # Verify custom title was applied
            item = cached_data["items"][0]
            assert item["properties"]["title"] == "Custom Test Title"


@patch("app.tasks.stac_tasks.get_db")
def test_generate_stac_preview_task_project_not_found(mock_get_db, db: Session):
    """Test STAC preview generation task with non-existent project."""
    # Setup
    mock_get_db.return_value.__enter__.return_value = db

    fake_project_id = str(uuid4())

    # Call the task - should raise an exception
    with pytest.raises(Exception) as exc_info:
        generate_stac_preview_task(fake_project_id, db=db)

    # Verify it's a project not found error
    assert "Project not found" in str(exc_info.value)


@patch("app.tasks.stac_tasks.get_db")
def test_generate_stac_preview_task_exception_handling(mock_get_db, db: Session):
    """Test STAC preview generation task exception handling."""
    # Setup
    mock_get_db.return_value.__enter__.return_value = db

    # Create project with flight and data product so STACGenerator validation passes
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Mock STACGenerator to raise an exception after validation
    with patch("app.utils.STACGenerator.STACGenerator") as mock_stac_gen:
        mock_stac_gen.side_effect = Exception("Test exception")

        # Call the task - should raise the exception
        with pytest.raises(Exception) as exc_info:
            generate_stac_preview_task(str(project.id), db=db)

        # Verify the exception message
        assert "Test exception" in str(exc_info.value)


@patch("app.tasks.stac_tasks.get_db")
def test_publish_stac_catalog_task_success(mock_get_db, db: Session):
    """Test successful STAC catalog publication task."""
    # Setup
    mock_get_db.return_value.__enter__.return_value = db

    # Create project with data
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock settings to use temp directory
        with patch.object(settings, "STATIC_DIR", temp_dir):
            # Mock the STAC collection manager to avoid actual API calls
            with patch("app.tasks.stac_tasks.STACCollectionManager") as mock_scm:
                mock_report = MagicMock()
                mock_report.is_published = True
                mock_report.collection_id = project.id
                mock_scm.return_value.publish_to_catalog.return_value = mock_report

                # Call the task
                result = publish_stac_catalog_task(str(project.id), db=db)

                # Verify result structure (STAC data, not status response)
                assert "collection_id" in result
                assert str(result["collection_id"]) == str(project.id)
                assert "collection" in result
                assert "items" in result
                assert result["is_published"] is True

                # Verify cache file was created and marked as published
                cache_path = get_stac_cache_path(project.id)
                assert cache_path.exists()

                # Verify cache content shows published status
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                assert cached_data["is_published"] is True


@patch("app.tasks.stac_tasks.get_db")
def test_publish_stac_catalog_task_with_parameters(mock_get_db, db: Session):
    """Test STAC catalog publication task with scientific metadata and custom titles."""
    # Setup
    mock_get_db.return_value.__enter__.return_value = db

    # Create project with data
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Parameters
    sci_doi = "10.1000/publish456"
    sci_citation = "Publish, Author, et al. (2023). Published Dataset. Publish Journal, 2(1), 5-20."
    custom_titles = {str(data_product.obj.id): "Custom Published Title"}

    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock settings to use temp directory
        with patch.object(settings, "STATIC_DIR", temp_dir):
            # Mock the STAC collection manager and project update
            with patch("app.tasks.stac_tasks.STACCollectionManager") as mock_scm, patch(
                "app.crud.project.update_project_visibility"
            ) as mock_update:

                mock_report = MagicMock()
                mock_report.is_published = True
                mock_report.collection_id = project.id
                mock_scm.return_value.publish_to_catalog.return_value = mock_report
                mock_update.return_value = True

                # Call the task
                result = publish_stac_catalog_task(
                    str(project.id),
                    sci_doi=sci_doi,
                    sci_citation=sci_citation,
                    custom_titles=custom_titles,
                    db=db,
                )

                # Verify result structure
                assert "collection_id" in result
                assert str(result["collection_id"]) == str(project.id)
                assert result["is_published"] is True

                # Verify cache file includes scientific metadata
                cache_path = get_stac_cache_path(project.id)
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                assert cached_data["collection"]["sci:doi"] == sci_doi
                assert cached_data["collection"]["sci:citation"] == sci_citation


@patch("app.tasks.stac_tasks.get_db")
def test_publish_stac_catalog_task_project_not_found(mock_get_db, db: Session):
    """Test STAC catalog publication task with non-existent project."""
    # Setup
    mock_get_db.return_value.__enter__.return_value = db

    fake_project_id = str(uuid4())

    # Call the task - should raise an exception
    with pytest.raises(Exception) as exc_info:
        publish_stac_catalog_task(fake_project_id, db=db)

    # Verify it's a project not found error
    assert "Project not found" in str(exc_info.value)


@patch("app.tasks.stac_tasks.get_db")
def test_publish_stac_catalog_task_exception_handling(mock_get_db, db: Session):
    """Test STAC catalog publication task exception handling."""
    # Setup
    mock_get_db.return_value.__enter__.return_value = db

    # Create project with flight and data product so STACGenerator validation passes
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(db, project=project, flight=flight)

    # Mock STACGenerator to raise an exception after validation
    with patch("app.utils.STACGenerator.STACGenerator") as mock_stac_gen:
        mock_stac_gen.side_effect = Exception("Publication failed")

        # Call the task - should raise the exception
        with pytest.raises(Exception) as exc_info:
            publish_stac_catalog_task(str(project.id), db=db)

        # Verify the exception message
        assert "Publication failed" in str(exc_info.value)


def test_cache_directory_creation():
    """Test that cache directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock settings to use temp directory
        with patch.object(settings, "STATIC_DIR", temp_dir):
            project_id = uuid4()
            cache_path = get_stac_cache_path(project_id)

            # get_stac_cache_path should create the directory automatically
            assert cache_path.parent.exists()

            # Should be able to write to cache file
            test_data = {"test": "data"}
            with open(cache_path, "w") as f:
                json.dump(test_data, f, cls=UUIDEncoder)

            # Should be able to read from cache file
            with open(cache_path, "r") as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data


@patch("app.tasks.stac_tasks.get_db")
def test_task_with_failed_items(mock_get_db, db: Session, monkeypatch):
    """Test STAC tasks handle failed items correctly."""
    # Setup
    mock_get_db.return_value.__enter__.return_value = db

    # Create project with data that will fail
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    data_product = SampleDataProduct(
        db, project=project, flight=flight, data_type="point_cloud"
    )

    # Mock pdal_to_stac.create_item to raise a ValueError for point cloud processing
    def mock_create_item(*args, **kwargs):
        raise ValueError("Unable to process point cloud in task")

    monkeypatch.setattr("app.utils.pdal_to_stac.create_item", mock_create_item)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock settings to use temp directory
        with patch.object(settings, "STATIC_DIR", temp_dir):
            # Call the preview task
            result = generate_stac_preview_task(str(project.id), db=db)

            # Verify result includes failed items
            assert "collection_id" in result
            assert str(result["collection_id"]) == str(project.id)
            assert result["is_published"] is False

            # Should have failed items
            assert "failed_items" in result
            assert len(result["failed_items"]) == 1

            # Verify failed item details
            failed_item = result["failed_items"][0]
            assert failed_item["is_published"] is False
            assert "error" in failed_item
            assert "Unable to process point cloud" in failed_item["error"]["message"]

            # Verify cache file includes failed items
            cache_path = get_stac_cache_path(project.id)
            assert cache_path.exists()

            with open(cache_path, "r") as f:
                cached_data = json.load(f)
            assert "failed_items" in cached_data
            assert len(cached_data["failed_items"]) == 1
