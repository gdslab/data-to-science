import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, List, Union, Optional
from uuid import UUID

from geojson_pydantic import Feature, FeatureCollection
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.utils import create_project_field_preview
from app.utils.STACCollectionManager import STACCollectionManager
from app.core.config import settings
from app.tasks.stac_tasks import (
    generate_stac_preview,
    publish_stac_catalog,
    get_stac_cache_path,
)


logger = logging.getLogger("__name__")

router = APIRouter()


@router.post("", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create new project for current user."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo accounts cannot create projects",
        )
    try:
        project = crud.project.create_with_owner(
            db,
            obj_in=project_in,
            owner_id=current_user.id,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create project",
        )
    if project["response_code"] != status.HTTP_201_CREATED:
        raise HTTPException(
            status_code=project["response_code"], detail=project["message"]
        )
    if not project["result"] or not project["result"].id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create project",
        )
    # Create preview image for project field boundary - skip if running tests
    if os.environ.get("RUNNING_TESTS") != "1":
        project_in_db = crud.project.get_user_project(
            db, user_id=current_user.id, project_id=project["result"].id
        )
        if project_in_db["result"]:
            try:
                if project_in_db["result"].field:
                    features: List[Feature] = [Feature(**project_in_db["result"].field)]
                    create_project_field_preview(project["result"].id, features)
            except Exception:
                logger.exception("Unable to create preview map")
    return project["result"]


@router.get("/{project_id}", response_model=Union[schemas.Project, FeatureCollection])
def read_project(
    project_id: UUID,
    format: str = Query("json", pattern="^(json|geojson)$"),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
    project: schemas.Project = Depends(deps.can_read_project),
) -> Any:
    """Retrieve project by id."""
    if format == "geojson":
        return {"type": "FeatureCollection", "features": [project.field]}
    else:
        return project


@router.get("", response_model=Union[List[schemas.project.Projects], FeatureCollection])
def read_projects(
    edit_only: bool = False,
    has_raster: bool = False,
    include_all: bool = False,
    format: str = Query("json", pattern="^(json|geojson)$"),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve list of projects current user belongs to."""
    projects = crud.project.get_user_projects(
        db,
        user=current_user,
        has_raster=has_raster,
        include_all=include_all,
    )

    if format == "geojson":
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [project.centroid.x, project.centroid.y],
                    },
                    "properties": {
                        "id": project.id,
                        "title": project.title,
                        "description": project.description,
                    },
                }
                for project in projects
            ],
        }
    else:
        return projects


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
            "sci_doi": metadata_request.sci_doi,
            "sci_citation": metadata_request.sci_citation,
            "license": metadata_request.license,
            "custom_titles": metadata_request.custom_titles,
            "cached_stac_metadata": cached_stac_metadata,
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
            "sci_doi": metadata_request.sci_doi,
            "sci_citation": metadata_request.sci_citation,
            "license": metadata_request.license,
            "custom_titles": metadata_request.custom_titles,
            "cached_stac_metadata": cached_stac_metadata,
        },
    )

    return {
        "message": "STAC catalog publication started",
        "task_id": task.id,
        "project_id": str(project_id),
    }


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: UUID,
    project_in: schemas.ProjectUpdate,
    project: models.Project = Depends(deps.can_read_write_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update project if current user is project owner or member."""
    if project_in.planting_date and project.harvest_date:
        if project.harvest_date < project_in.planting_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[
                    {
                        "loc": ["body", "harvest_date"],
                        "msg": "End date must be after start date.",
                        "type": "value_error",
                    }
                ],
            )

    if project_in.harvest_date and project.planting_date:
        if project_in.harvest_date < project.planting_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[
                    {
                        "loc": ["body", "harvest_date"],
                        "msg": "End date must be after start date.",
                        "type": "value_error",
                    }
                ],
            )
    updated_project = crud.project.update_project(
        db,
        project_id=project_id,
        project_obj=project,
        project_in=project_in,
        user_id=current_user.id,
    )
    if updated_project["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=updated_project["response_code"],
            detail=updated_project["message"],
        )
    return updated_project["result"]


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


@router.delete("/{project_id}", response_model=schemas.Project)
def deactivate_project(
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_write_delete_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    # Check if project is published
    if project.is_published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate project when it is published in a STAC catalog",
        )

    deactivated_project = crud.project.deactivate(
        db, project_id=project.id, user_id=current_user.id
    )
    if not deactivated_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to deactivate"
        )
    return deactivated_project


@router.post("/{project_id}/like", status_code=status.HTTP_201_CREATED)
def create_project_like(
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create project like."""
    project_like_in_db = crud.project_like.get_by_project_id_and_user_id(
        db, project_id=project_id, user_id=current_user.id
    )
    if project_like_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Project already bookmarked"
        )
    project_like_in = schemas.ProjectLikeCreate(
        project_id=project_id,
        user_id=current_user.id,
    )
    project_like = crud.project_like.create(db, obj_in=project_like_in)
    if not project_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to create like"
        )

    return {"message": "Project bookmarked"}


@router.delete("/{project_id}/like", status_code=status.HTTP_200_OK)
def delete_project_like(
    project_id: UUID,
    project: models.Project = Depends(deps.can_read_project),
    current_user: models.User = Depends(deps.get_current_approved_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Delete project like."""
    project_like_in_db = crud.project_like.get_by_project_id_and_user_id(
        db, project_id=project_id, user_id=current_user.id
    )
    if not project_like_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to delete like"
        )
    project_like = crud.project_like.remove(db, id=project_like_in_db.id)

    if not project_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to delete like"
        )

    return {"message": "Project unbookmarked"}


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
            collection_url = f"{settings.STAC_BROWSER_URL}/collections/{project_id}"
            # Add URL to each item
            for item in items:
                item["browser_url"] = (
                    f"{settings.STAC_BROWSER_URL}/collections/{project_id}/items/{item['id']}"
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
