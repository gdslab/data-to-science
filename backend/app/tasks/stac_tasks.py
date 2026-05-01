import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
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

from pystac import Item

from app import crud, models, schemas
from app.api.deps import get_db
from app.api.utils import get_static_dir
from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.job import Job as JobModel
from app.schemas.job import Status
from app.utils.job_manager import JobManager
from app.utils.s3 import (
    is_s3_configured,
    build_s3_key,
    upload_file_to_s3,
    delete_s3_objects,
    parse_s3_key_from_url,
)

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


def _upload_to_s3_and_rewrite_hrefs(
    db: Session,
    items: List[Item],
    flights: List[models.Flight],
    include_raw_data_links: Optional[List[str]],
) -> List[str]:
    """Upload successful data products (and raw data) to S3 and rewrite STAC item hrefs.

    Called after STAC generation, only for items that succeeded.
    Returns a list of S3 keys that were uploaded (for rollback on failure).

    Raises on upload failure so the caller can handle rollback.
    """
    upload_dir = get_static_dir()
    uploaded_s3_keys: List[str] = []

    # Build a lookup from data_product_id -> data_product model
    dp_lookup: Dict[str, models.DataProduct] = {}
    for flight in flights:
        for dp in flight.data_products:
            dp_lookup[str(dp.id)] = dp

    # Collect flight IDs that have items with derived_from links (for raw data upload)
    include_raw_data_set = set(include_raw_data_links) if include_raw_data_links else set()
    flights_needing_raw_data: set = set()

    # Upload data product files and rewrite asset hrefs
    for item in items:
        dp = dp_lookup.get(item.id)
        if not dp:
            logger.warning(f"Data product not found for item {item.id}, skipping S3 upload")
            continue

        # Skip if already uploaded (idempotent for backfill)
        if dp.s3_url:
            s3_url = dp.s3_url
        else:
            # Upload the data product file
            s3_key = build_s3_key(dp.filepath, upload_dir)
            s3_url = upload_file_to_s3(dp.filepath, s3_key)
            uploaded_s3_keys.append(s3_key)

            # Update DB
            crud.data_product.update_s3_url(db, data_product_id=dp.id, s3_url=s3_url)

        # Rewrite the asset href
        if item.id in item.assets:
            item.assets[item.id].href = s3_url

        # Rewrite external viewer link if present
        for link in item.links:
            if link.rel == "external" and hasattr(link, "href"):
                # Replace the url= query parameter with the S3 URL
                if settings.EXTERNAL_VIEWER_URL:
                    link.target = f"{settings.EXTERNAL_VIEWER_URL}?url={s3_url}"

        # Track if this item needs raw data uploaded
        if item.id in include_raw_data_set:
            flights_needing_raw_data.add(dp.flight_id)

    # Upload raw data files for flights that have derived_from links
    if flights_needing_raw_data:
        for flight_id in flights_needing_raw_data:
            # Query raw data for this flight
            raw_data_list = crud.raw_data.get_multi_by_flight(
                db=db, flight_id=flight_id, upload_dir=upload_dir,
            )

            for rd in raw_data_list:
                local_url = getattr(rd, "url", None)
                if not local_url:
                    continue

                # Skip if already uploaded (idempotent for backfill)
                if rd.s3_url:
                    s3_url = rd.s3_url
                else:
                    # Upload raw data file
                    s3_key = build_s3_key(rd.filepath, upload_dir)
                    s3_url = upload_file_to_s3(rd.filepath, s3_key)
                    uploaded_s3_keys.append(s3_key)

                    # Update DB
                    crud.raw_data.update_s3_url(db, raw_data_id=rd.id, s3_url=s3_url)

                # Rewrite derived_from links on items that reference this flight
                for item in items:
                    dp = dp_lookup.get(item.id)
                    if dp and dp.flight_id == flight_id:
                        for link in item.links:
                            if link.rel == "derived_from" and link.href == local_url:
                                link.target = s3_url

    return uploaded_s3_keys


def _rollback_s3_uploads(db: Session, project_id: UUID, uploaded_s3_keys: List[str]) -> None:
    """Clean up S3 uploads and DB records on publish failure.

    Preserves s3_url columns when the S3 delete does not fully succeed so the
    orphaned objects can be cleaned up on a future retry.
    """
    try:
        if uploaded_s3_keys and not delete_s3_objects(uploaded_s3_keys):
            logger.error(
                f"S3 rollback did not fully succeed for project {project_id}; "
                f"preserving s3_url columns for retry"
            )
            return
        crud.data_product.clear_s3_urls_for_project(db, project_id=project_id)
        crud.raw_data.clear_s3_urls_for_project(db, project_id=project_id)
    except Exception:
        logger.exception("Failed to rollback S3 uploads")


@celery_app.task(name="generate_stac_preview_task", bind=True)
def generate_stac_preview(
    self,
    project_id: str,
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    sci_doi: Optional[str] = None,
    sci_citation: Optional[str] = None,
    license: Optional[str] = None,
    custom_titles: Optional[Dict[str, str]] = None,
    cached_stac_metadata: Optional[Dict] = None,
    include_raw_data_links: Optional[List[str]] = None,
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
            contact_name=contact_name,
            contact_email=contact_email,
            sci_doi=sci_doi,
            sci_citation=sci_citation,
            license=license,
            custom_titles=custom_titles,
            cached_stac_metadata=cached_stac_metadata,
            include_raw_data_links=include_raw_data_links,
        )
        collection = sg.collection
        items = sg.items
        failed_items = sg.failed_items

        # Prepare response data
        collection_dict = collection.to_dict()
        items_dicts = [item.to_dict() for item in items]
        response_data = {
            "collection_id": project_id,
            "collection": collection_dict,
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
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    sci_doi: Optional[str] = None,
    sci_citation: Optional[str] = None,
    license: Optional[str] = None,
    custom_titles: Optional[Dict[str, str]] = None,
    cached_stac_metadata: Optional[Dict] = None,
    include_raw_data_links: Optional[List[str]] = None,
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
            contact_name=contact_name,
            contact_email=contact_email,
            sci_doi=sci_doi,
            sci_citation=sci_citation,
            license=license,
            custom_titles=custom_titles,
            cached_stac_metadata=cached_stac_metadata,
            include_raw_data_links=include_raw_data_links,
        )
        collection = sg.collection
        items = sg.items
        failed_items = sg.failed_items

        # Upload successful items to S3 and rewrite asset hrefs
        uploaded_s3_keys: List[str] = []
        if is_s3_configured() and len(items) > 0:
            uploaded_s3_keys = _upload_to_s3_and_rewrite_hrefs(
                db, items, sg.flights, include_raw_data_links,
            )

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

        # Rollback S3 uploads if any were made
        if is_s3_configured():
            _rollback_s3_uploads(
                db, project_uuid,
                uploaded_s3_keys if "uploaded_s3_keys" in locals() else [],
            )

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
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    sci_doi: Optional[str] = None,
    sci_citation: Optional[str] = None,
    license: Optional[str] = None,
    custom_titles: Optional[Dict[str, str]] = None,
    cached_stac_metadata: Optional[Dict] = None,
    include_raw_data_links: Optional[List[str]] = None,
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
            contact_name=contact_name,
            contact_email=contact_email,
            sci_doi=sci_doi,
            sci_citation=sci_citation,
            license=license,
            custom_titles=custom_titles,
            cached_stac_metadata=cached_stac_metadata,
            include_raw_data_links=include_raw_data_links,
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
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    sci_doi: Optional[str] = None,
    sci_citation: Optional[str] = None,
    license: Optional[str] = None,
    custom_titles: Optional[Dict[str, str]] = None,
    cached_stac_metadata: Optional[Dict] = None,
    include_raw_data_links: Optional[List[str]] = None,
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
            contact_name=contact_name,
            contact_email=contact_email,
            sci_doi=sci_doi,
            sci_citation=sci_citation,
            license=license,
            custom_titles=custom_titles,
            cached_stac_metadata=cached_stac_metadata,
            include_raw_data_links=include_raw_data_links,
        )
        collection = sg.collection
        items = sg.items
        failed_items = sg.failed_items

        # Upload successful items to S3 and rewrite asset hrefs
        uploaded_s3_keys: List[str] = []
        if is_s3_configured() and len(items) > 0:
            uploaded_s3_keys = _upload_to_s3_and_rewrite_hrefs(
                db, items, sg.flights, include_raw_data_links,
            )

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

        # Rollback S3 uploads if any were made
        if is_s3_configured():
            _rollback_s3_uploads(
                db, project_uuid,
                uploaded_s3_keys if "uploaded_s3_keys" in locals() else [],
            )

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
