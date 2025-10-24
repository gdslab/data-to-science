import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urljoin
from uuid import UUID


# Custom JSON encoder to handle UUIDs and datetimes
class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.job import Job as JobModel
from app.schemas.job import Status
from app.utils.job_manager import JobManager

# Import these at module level for testing/mocking purposes
# They will be imported again inside functions to avoid circular imports during normal operation
try:
    from app.utils.stac.STACGenerator import STACGenerator
    from app.utils.stac.STACCollectionManager import STACCollectionManager
except ImportError:
    # Handle circular import gracefully
    STACGenerator = None
    STACCollectionManager = None

logger = get_task_logger(__name__)


def get_stac_cache_path(project_id: UUID) -> Path:
    """Get the path to the STAC cache file for a project."""
    if os.environ.get("RUNNING_TESTS") == "1":
        static_dir = settings.TEST_STATIC_DIR
    else:
        static_dir = settings.STATIC_DIR

    project_dir = Path(static_dir) / "projects" / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir / "stac.json"


def get_stac_timestamp(job: Optional[JobModel] = None) -> Optional[str]:
    """Get the timestamp for a job."""
    if job and job.end_time:
        return job.end_time.isoformat()
    elif job and job.start_time:
        return job.start_time.isoformat()
    else:
        return None


@celery_app.task(name="generate_stac_preview_task", bind=True)
def generate_stac_preview(
    self,
    project_id: str,
    sci_doi: Optional[str] = None,
    sci_citation: Optional[str] = None,
    license: Optional[str] = None,
    custom_titles: Optional[Dict[str, str]] = None,
    cached_stac_metadata: Optional[Dict] = None,
) -> Dict:
    """Generate STAC preview metadata for a project without publishing."""
    db: Session = next(get_db())
    project_uuid = UUID(project_id)

    # Create job for tracking
    job = JobManager(job_name="stac_preview")
    job.update(status=Status.INPROGRESS, extra={"project_id": str(project_uuid)})

    try:
        # Generate STAC collection and items
        sg = STACGenerator(
            db,
            project_id=project_uuid,
            sci_doi=sci_doi,
            sci_citation=sci_citation,
            license=license,
            custom_titles=custom_titles,
            cached_stac_metadata=cached_stac_metadata,
        )
        collection = sg.collection
        items = sg.items
        failed_items = sg.failed_items

        # Prepare response data
        items_dicts = [item.to_dict() for item in items]
        response_data = {
            "collection_id": project_id,
            "collection": collection.to_dict(),
            "items": items_dicts,
            "is_published": False,
            "timestamp": get_stac_timestamp(job.job),
        }

        # Add browser URLs if configured
        if settings.STAC_BROWSER_URL:
            response_data["collection_url"] = urljoin(
                str(settings.STAC_BROWSER_URL), f"collections/{project_id}"
            )
            # Add URL to each item
            for item_dict in items_dicts:
                item_dict["browser_url"] = urljoin(
                    str(settings.STAC_BROWSER_URL),
                    f"collections/{project_id}/items/{item_dict['id']}",
                )

        # Add failed items if any exist
        if failed_items:
            response_data["failed_items"] = [item.model_dump() for item in failed_items]

        # Cache the result
        cache_path = get_stac_cache_path(project_uuid)
        with open(cache_path, "w") as f:
            json.dump(response_data, f, indent=2, cls=UUIDEncoder)

        job.update(status=Status.SUCCESS)
        logger.info(f"STAC preview generated successfully for project {project_id}")

        return response_data

    except Exception as e:
        logger.exception(
            f"Failed to generate STAC preview for project {project_id}: {str(e)}"
        )
        job.update(status=Status.FAILED)

        # Cache error response
        error_response = {
            "collection_id": project_id,
            "error": str(e),
            "timestamp": get_stac_timestamp(job.job),
        }

        try:
            cache_path = get_stac_cache_path(project_uuid)
            with open(cache_path, "w") as f:
                json.dump(error_response, f, indent=2, cls=UUIDEncoder)
        except Exception:
            logger.exception("Failed to cache error response")

        raise


@celery_app.task(name="publish_stac_catalog_task", bind=True)
def publish_stac_catalog(
    self,
    project_id: str,
    sci_doi: Optional[str] = None,
    sci_citation: Optional[str] = None,
    license: Optional[str] = None,
    custom_titles: Optional[Dict[str, str]] = None,
    cached_stac_metadata: Optional[Dict] = None,
) -> Dict:
    """Publish project to STAC catalog."""
    db: Session = next(get_db())
    project_uuid = UUID(project_id)

    # Create job for tracking
    job = JobManager(job_name="stac_publish")
    job.update(status=Status.INPROGRESS, extra={"project_id": str(project_uuid)})

    try:
        # Generate STAC collection and items
        sg = STACGenerator(
            db,
            project_id=project_uuid,
            sci_doi=sci_doi,
            sci_citation=sci_citation,
            license=license,
            custom_titles=custom_titles,
            cached_stac_metadata=cached_stac_metadata,
        )
        collection = sg.collection
        items = sg.items
        failed_items = sg.failed_items

        # Publish to catalog if we have successful items
        stac_report = None
        if len(items) > 0:
            scm = STACCollectionManager(
                collection_id=str(project_uuid), collection=collection, items=items
            )
            stac_report = scm.publish_to_catalog()

            # Update project to published
            crud.project.update_project_visibility(
                db, project_id=project_uuid, is_public=True
            )
        else:
            # No successful items to publish
            stac_report = schemas.STACReport(
                collection_id=project_uuid,
                items=[],
                is_published=False,
                collection_url=None,
                error=None,
            )

        # Add failed items to the report
        if failed_items:
            stac_report.items.extend(failed_items)

        # Prepare response data
        items_dicts = [item.to_dict() for item in items]
        response_data = {
            "collection_id": project_id,
            "collection": collection.to_dict(),
            "items": items_dicts,
            "is_published": len(items) > 0,
            "timestamp": get_stac_timestamp(job.job),
        }

        # Add browser URLs if configured
        if settings.STAC_BROWSER_URL and len(items) > 0:
            response_data["collection_url"] = urljoin(
                str(settings.STAC_BROWSER_URL), f"collections/{project_id}"
            )
            for item_dict in items_dicts:
                item_dict["browser_url"] = urljoin(
                    str(settings.STAC_BROWSER_URL),
                    f"collections/{project_id}/items/{item_dict['id']}",
                )

        # Add failed items if any exist
        if failed_items:
            response_data["failed_items"] = [item.model_dump() for item in failed_items]

        # Cache the result
        cache_path = get_stac_cache_path(project_uuid)
        with open(cache_path, "w") as f:
            json.dump(response_data, f, indent=2, cls=UUIDEncoder)

        job.update(status=Status.SUCCESS)
        logger.info(f"STAC catalog published successfully for project {project_id}")

        return response_data

    except Exception as e:
        logger.exception(
            f"Failed to publish STAC catalog for project {project_id}: {str(e)}"
        )
        job.update(status=Status.FAILED)

        # Try to rollback if we have a collection manager
        try:
            if "scm" in locals():
                scm.remove_from_catalog()
        except Exception:
            logger.exception("Failed to rollback STAC publication")

        # Cache error response
        error_response = {
            "collection_id": project_id,
            "error": str(e),
            "timestamp": get_stac_timestamp(job.job),
        }

        try:
            cache_path = get_stac_cache_path(project_uuid)
            with open(cache_path, "w") as f:
                json.dump(error_response, f, indent=2, cls=UUIDEncoder)
        except Exception:
            logger.exception("Failed to cache error response")

        raise


# Non-Celery functions for testing (duplicate the logic without Celery decorators)
def generate_stac_preview_task(
    project_id: str,
    sci_doi: Optional[str] = None,
    sci_citation: Optional[str] = None,
    license: Optional[str] = None,
    custom_titles: Optional[Dict[str, str]] = None,
    cached_stac_metadata: Optional[Dict] = None,
    db: Optional[Session] = None,
) -> Dict:
    """Non-Celery function for testing STAC preview generation."""
    from app.api.deps import get_db
    from app.schemas.job import Status
    from app.utils.job_manager import JobManager
    from app.utils.stac.STACGenerator import STACGenerator

    if db is None:
        db = next(get_db())
    project_uuid = UUID(project_id)

    # Create job for tracking
    job = JobManager(job_name="stac_preview")
    job.update(status=Status.INPROGRESS, extra={"project_id": str(project_uuid)})

    try:
        # Generate STAC collection and items
        sg = STACGenerator(
            db,
            project_id=project_uuid,
            sci_doi=sci_doi,
            sci_citation=sci_citation,
            license=license,
            custom_titles=custom_titles,
            cached_stac_metadata=cached_stac_metadata,
        )
        collection = sg.collection
        items = sg.items
        failed_items = sg.failed_items

        # Prepare response data
        items_dicts = [item.to_dict() for item in items]
        response_data = {
            "collection_id": project_id,
            "collection": collection.to_dict(),
            "items": items_dicts,
            "is_published": False,
            "timestamp": get_stac_timestamp(job.job),
        }

        # Add browser URLs if configured
        if settings.STAC_BROWSER_URL:
            response_data["collection_url"] = urljoin(
                str(settings.STAC_BROWSER_URL), f"collections/{project_id}"
            )
            # Add URL to each item
            for item_dict in items_dicts:
                item_dict["browser_url"] = urljoin(
                    str(settings.STAC_BROWSER_URL),
                    f"collections/{project_id}/items/{item_dict['id']}",
                )

        # Add failed items if any exist
        if failed_items:
            response_data["failed_items"] = [item.model_dump() for item in failed_items]

        # Cache the result
        cache_path = get_stac_cache_path(project_uuid)
        with open(cache_path, "w") as f:
            json.dump(response_data, f, indent=2, cls=UUIDEncoder)

        job.update(status=Status.SUCCESS)
        logger.info(f"STAC preview generated successfully for project {project_id}")

        return response_data

    except Exception as e:
        logger.exception(
            f"Failed to generate STAC preview for project {project_id}: {str(e)}"
        )
        job.update(status=Status.FAILED)

        # Cache error response
        error_response = {
            "collection_id": project_id,
            "error": str(e),
            "timestamp": get_stac_timestamp(job.job),
        }

        try:
            cache_path = get_stac_cache_path(project_uuid)
            with open(cache_path, "w") as f:
                json.dump(error_response, f, indent=2, cls=UUIDEncoder)
        except Exception:
            logger.exception("Failed to cache error response")

        raise


def publish_stac_catalog_task(
    project_id: str,
    sci_doi: Optional[str] = None,
    sci_citation: Optional[str] = None,
    license: Optional[str] = None,
    custom_titles: Optional[Dict[str, str]] = None,
    cached_stac_metadata: Optional[Dict] = None,
    db: Optional[Session] = None,
) -> Dict:
    """Non-Celery function for testing STAC catalog publication."""
    from app.api.deps import get_db
    from app.schemas.job import Status
    from app.utils.job_manager import JobManager
    from app.utils.stac.STACGenerator import STACGenerator
    from app.utils.stac.STACCollectionManager import STACCollectionManager
    from app import crud, schemas

    if db is None:
        db = next(get_db())
    project_uuid = UUID(project_id)

    # Create job for tracking
    job = JobManager(job_name="stac_publish")
    job.update(status=Status.INPROGRESS, extra={"project_id": str(project_uuid)})

    try:
        # Generate STAC collection and items
        sg = STACGenerator(
            db,
            project_id=project_uuid,
            sci_doi=sci_doi,
            sci_citation=sci_citation,
            license=license,
            custom_titles=custom_titles,
            cached_stac_metadata=cached_stac_metadata,
        )
        collection = sg.collection
        items = sg.items
        failed_items = sg.failed_items

        # Publish to catalog if we have successful items
        stac_report = None
        if len(items) > 0:
            scm = STACCollectionManager(
                collection_id=str(project_uuid), collection=collection, items=items
            )
            stac_report = scm.publish_to_catalog()

            # Update project to published
            crud.project.update_project_visibility(
                db, project_id=project_uuid, is_public=True
            )
        else:
            # No successful items to publish
            stac_report = schemas.STACReport(
                collection_id=project_uuid,
                items=[],
                is_published=False,
                collection_url=None,
                error=None,
            )

        # Add failed items to the report
        if failed_items:
            stac_report.items.extend(failed_items)

        # Prepare response data
        items_dicts = [item.to_dict() for item in items]
        response_data = {
            "collection_id": project_id,
            "collection": collection.to_dict(),
            "items": items_dicts,
            "is_published": len(items) > 0,
            "timestamp": get_stac_timestamp(job.job),
        }

        # Add browser URLs if configured
        if settings.STAC_BROWSER_URL and len(items) > 0:
            response_data["collection_url"] = urljoin(
                str(settings.STAC_BROWSER_URL), f"collections/{project_id}"
            )
            for item_dict in items_dicts:
                item_dict["browser_url"] = urljoin(
                    str(settings.STAC_BROWSER_URL),
                    f"collections/{project_id}/items/{item_dict['id']}",
                )

        # Add failed items if any exist
        if failed_items:
            response_data["failed_items"] = [item.model_dump() for item in failed_items]

        # Cache the result
        cache_path = get_stac_cache_path(project_uuid)
        with open(cache_path, "w") as f:
            json.dump(response_data, f, indent=2, cls=UUIDEncoder)

        job.update(status=Status.SUCCESS)
        logger.info(f"STAC catalog published successfully for project {project_id}")

        return response_data

    except Exception as e:
        logger.exception(
            f"Failed to publish STAC catalog for project {project_id}: {str(e)}"
        )
        job.update(status=Status.FAILED)

        # Try to rollback if we have a collection manager
        try:
            if "scm" in locals():
                scm.remove_from_catalog()
        except Exception:
            logger.exception("Failed to rollback STAC publication")

        # Cache error response
        error_response = {
            "collection_id": project_id,
            "error": str(e),
            "timestamp": get_stac_timestamp(job.job),
        }

        try:
            cache_path = get_stac_cache_path(project_uuid)
            with open(cache_path, "w") as f:
                json.dump(error_response, f, indent=2, cls=UUIDEncoder)
        except Exception:
            logger.exception("Failed to cache error response")

        raise
