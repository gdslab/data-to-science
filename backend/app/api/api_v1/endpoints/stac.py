import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from urllib.parse import urljoin
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.tasks.stac_tasks import (
    generate_stac_preview,
    publish_stac_catalog,
    get_stac_cache_path,
)
from app.utils.s3 import delete_s3_objects, is_s3_configured, parse_s3_key_from_url
from app.utils.stac.STACCollectionManager import STACCollectionManager


logger = logging.getLogger(__name__)

router = APIRouter()


class S3CleanupError(Exception):
    """Raised when the S3 cleanup step of unpublish does not fully succeed.

    The endpoint converts this into a 503 with a generic message so the user
    can retry once S3 connectivity is restored. The s3_url columns are left
    intact so orphaned objects remain trackable.
    """


def _cleanup_s3_for_project(db: Session, project_id: UUID) -> None:
    """Delete S3 copies of data products and raw data for a project, then clear s3_url columns.

    Raises S3CleanupError if the S3 delete does not fully succeed. The s3_url
    columns are preserved in that case so the orphaned objects can be cleaned
    up on a future retry.
    """
    s3_keys = []

    # Collect S3 keys from data products
    data_products = crud.data_product.get_data_products_with_s3_urls_for_project(
        db, project_id=project_id
    )
    for dp in data_products:
        try:
            s3_keys.append(parse_s3_key_from_url(dp.s3_url))
        except ValueError:
            logger.warning(f"Could not parse S3 key from URL: {dp.s3_url}")

    # Collect S3 keys from raw data
    raw_data_list = crud.raw_data.get_raw_data_with_s3_urls_for_project(
        db, project_id=project_id
    )
    for rd in raw_data_list:
        try:
            s3_keys.append(parse_s3_key_from_url(rd.s3_url))
        except ValueError:
            logger.warning(f"Could not parse S3 key from URL: {rd.s3_url}")

    # Delete from S3; preserve s3_url columns if delete fails so we can retry
    if s3_keys and not delete_s3_objects(s3_keys):
        raise S3CleanupError(
            f"S3 cleanup did not fully succeed for project {project_id}"
        )

    # Clear s3_url columns in DB
    crud.data_product.clear_s3_urls_for_project(db, project_id=project_id)
    crud.raw_data.clear_s3_urls_for_project(db, project_id=project_id)


@router.get(
    "/{project_id}/stac-cache", response_model=Union[schemas.STACResponse, dict]
)
def get_cached_stac_metadata(
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
) -> Any:
    """Get cached STAC metadata for a project."""
    cache_path = get_stac_cache_path(project_id)

    if not cache_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No cached STAC metadata found. Please generate it first.",
        )

    try:
        with open(cache_path, "r") as f:
            cached_data = json.load(f)

        # Add browser URLs if configured and not already present
        if settings.STAC_BROWSER_URL and "collection_url" not in cached_data:
            cached_data["collection_url"] = urljoin(
                str(settings.STAC_BROWSER_URL), f"collections/{project_id}"
            )
            # Add URL to each item if not already present
            if "items" in cached_data:
                for item in cached_data["items"]:
                    if "browser_url" not in item:
                        item["browser_url"] = urljoin(
                            str(settings.STAC_BROWSER_URL),
                            f"collections/{project_id}/items/{item['id']}",
                        )

        return cached_data
    except Exception as e:
        logger.exception(f"Failed to read cached STAC metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read cached STAC metadata",
        )


@router.post("/{project_id}/generate-stac-preview")
def generate_stac_preview_async(
    project_id: UUID,
    metadata_request: schemas.STACMetadataRequest,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Generate STAC preview metadata asynchronously."""
    # Check for cached STAC metadata to optimize generation
    cached_stac_metadata = None
    cache_path = get_stac_cache_path(project_id)
    try:
        if cache_path.exists():
            with open(cache_path, "r") as f:
                cached_stac_metadata = json.load(f)
    except Exception:
        logger.warning("Could not read cached STAC metadata for optimization")

    # Check if a STAC preview job is already running for this project
    # Exclude jobs older than 24 hours to prevent stale/failed jobs from blocking new ones
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    existing_jobs = crud.job.get_jobs_by_name_and_project_id(
        db,
        job_name="stac_preview",
        project_id=project_id,
        processing=True,
        cutoff_time=cutoff_time,
    )
    if existing_jobs:
        logger.info(
            f"STAC preview job already running for project {project_id}, returning existing job info"
        )
        # Try to return cached result if available
        if cached_stac_metadata:
            return {
                "message": "STAC preview already generated",
                "project_id": str(project_id),
                "cached_result": cached_stac_metadata,
            }

        # Return job in progress response
        return {
            "message": "STAC preview generation already in progress",
            "project_id": str(project_id),
            "task_id": str(existing_jobs[0].id),  # Return the existing job ID
        }

    # Start the background task
    task = generate_stac_preview.apply_async(
        args=[str(project_id)],
        kwargs={
            "contact_name": metadata_request.contact_name,
            "contact_email": metadata_request.contact_email,
            "sci_doi": metadata_request.sci_doi,
            "sci_citation": metadata_request.sci_citation,
            "license": metadata_request.license,
            "custom_titles": metadata_request.custom_titles,
            "cached_stac_metadata": cached_stac_metadata,
            "include_raw_data_links": metadata_request.include_raw_data_links,
        },
    )

    return {
        "message": "STAC preview generation started",
        "task_id": task.id,
        "project_id": str(project_id),
    }


@router.put("/{project_id}/publish-stac-async")
def publish_project_to_stac_catalog_async(
    project_id: UUID,
    metadata_request: schemas.STACMetadataRequest,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Publish project to STAC catalog asynchronously."""
    # Check for cached STAC metadata to optimize generation
    cached_stac_metadata = None
    cache_path = get_stac_cache_path(project_id)
    try:
        if cache_path.exists():
            with open(cache_path, "r") as f:
                cached_stac_metadata = json.load(f)
    except Exception:
        logger.warning("Could not read cached STAC metadata for optimization")

    # Check if a STAC publish job is already running for this project
    # Exclude jobs older than 24 hours to prevent stale/failed jobs from blocking new ones
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    existing_jobs = crud.job.get_jobs_by_name_and_project_id(
        db,
        job_name="stac_publish",
        project_id=project_id,
        processing=True,
        cutoff_time=cutoff_time,
    )
    if existing_jobs:
        logger.info(
            f"STAC publish job already running for project {project_id}, returning existing job info"
        )
        # Try to return cached result if available
        if cached_stac_metadata:
            return {
                "message": "Cached data from previous STAC publish job",
                "project_id": str(project_id),
                "cached_result": cached_stac_metadata,
            }

        # Return job in progress response
        return {
            "message": "STAC catalog publication already in progress",
            "project_id": str(project_id),
            "task_id": str(existing_jobs[0].id),  # Return the existing job ID
        }

    # Start the background task
    task = publish_stac_catalog.apply_async(
        args=[str(project_id)],
        kwargs={
            "contact_name": metadata_request.contact_name,
            "contact_email": metadata_request.contact_email,
            "sci_doi": metadata_request.sci_doi,
            "sci_citation": metadata_request.sci_citation,
            "license": metadata_request.license,
            "custom_titles": metadata_request.custom_titles,
            "cached_stac_metadata": cached_stac_metadata,
            "include_raw_data_links": metadata_request.include_raw_data_links,
        },
    )

    return {
        "message": "STAC catalog publication started",
        "task_id": task.id,
        "project_id": str(project_id),
    }


@router.delete("/{project_id}/delete-stac", response_model=schemas.Project)
def remove_project_from_stac_catalog(
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Remove project from STAC catalog."""
    # Check if project exists in STAC catalog
    scm = STACCollectionManager(collection_id=str(project_id))
    collection = scm.fetch_public_collection()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project not found in STAC catalog",
        )

    # Delete S3 copies of published data BEFORE catalog removal so a failure
    # leaves the project fully published and retriable rather than half-unpublished.
    if is_s3_configured():
        try:
            _cleanup_s3_for_project(db, project_id)
        except Exception:
            logger.exception(
                f"Failed to clean up S3 for project {project_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Could not clean up published data from the configured S3 "
                    "bucket. Please try again later."
                ),
            )

    # Remove project from STAC catalog
    try:
        scm.remove_from_catalog()
    except Exception:
        logger.exception(
            f"Failed to remove collection and items from STAC catalog for project {project_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove project from STAC catalog. Please try again later.",
        )

    # Delete STAC cache to prevent stale URLs on re-publish
    try:
        cache_path = get_stac_cache_path(project_id)
        if cache_path.exists():
            cache_path.unlink()
    except Exception:
        logger.exception(f"Failed to delete STAC cache for project {project_id}")

    # Update the project to unpublished and change all data products to private
    updated_project = crud.project.update_project_visibility(
        db, project_id=project_id, is_public=False
    )

    if not updated_project:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove project from STAC catalog. Please try again later.",
        )

    return updated_project


@router.get("/{project_id}/stac", response_model=schemas.STACResponse)
def get_project_stac_metadata(
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Get STAC metadata for a published project."""
    if not project.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is not published in STAC catalog",
        )

    try:
        # Fetch collection and items from STAC API
        scm = STACCollectionManager(collection_id=str(project_id))
        collection = scm.fetch_public_collection()
        items = scm.fetch_public_items_full()

        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="STAC collection not found",
            )

        # Add browser URLs if STAC_BROWSER_URL is configured
        collection_url = None
        if settings.STAC_BROWSER_URL:
            collection_url = urljoin(
                str(settings.STAC_BROWSER_URL), f"collections/{project_id}"
            )
            # Add URL to each item
            for item in items:
                item["browser_url"] = urljoin(
                    str(settings.STAC_BROWSER_URL),
                    f"collections/{project_id}/items/{item['id']}",
                )

        return {
            "collection_id": project_id,
            "collection": collection,
            "items": items,
            "is_published": True,
            "collection_url": collection_url,
        }
    except Exception as e:
        logger.exception(
            f"Failed to fetch STAC metadata for project {project_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch STAC metadata. Please try again later.",
        )
