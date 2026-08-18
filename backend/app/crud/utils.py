"""Checks shared by more than one CRUD module."""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied
from app.models.flight import Flight
from app.models.project import Project

# Deactivating anything inside a published project would leave the STAC catalog
# pointing at data the cleanup utilities are then free to remove for good, so
# the project has to be unpublished first.
PUBLISHED_PROJECT_DETAIL = (
    "Cannot deactivate project when it is published in a STAC catalog"
)
PUBLISHED_CONTENT_DETAIL = (
    "Cannot deactivate {item_type} when project is published in a STAC catalog"
)


def raise_if_project_published(db: Session, project_id: UUID) -> None:
    """Refuse to deactivate a project that is published in a STAC catalog.

    Args:
        db (Session): Database session.
        project_id (UUID): ID of the project being deactivated.

    Raises:
        PermissionDenied: If the project is published.
    """
    published_query = select(Project.is_published).where(Project.id == project_id)
    with db as session:
        is_published = session.scalar(published_query)

    if is_published:
        raise PermissionDenied(PUBLISHED_PROJECT_DETAIL)


def raise_if_owning_project_published(
    db: Session, model: Any, item_id: UUID, item_type: str
) -> None:
    """Refuse to deactivate a record inside a published project.

    Called by the deactivate methods rather than by their callers, so a record
    is protected no matter what reaches it: an endpoint, a background task, or
    a script. A record with no project left to check is allowed through, and the
    deactivate method reports it missing as it would have anyway.

    Args:
        db (Session): Database session.
        model (Any): Flight, DataProduct, or RawData model.
        item_id (UUID): ID of the record being deactivated.
        item_type (str): Type of record, used in the error message (e.g.,
            "flight").

    Raises:
        PermissionDenied: If the project the record belongs to is published.
    """
    published_query = select(Project.is_published).join(
        Flight, Flight.project_id == Project.id
    )
    if model is Flight:
        published_query = published_query.where(Flight.id == item_id)
    else:
        published_query = published_query.join(
            model, model.flight_id == Flight.id
        ).where(model.id == item_id)

    with db as session:
        is_published: Optional[bool] = session.scalar(published_query)

    if is_published:
        raise PermissionDenied(PUBLISHED_CONTENT_DETAIL.format(item_type=item_type))
