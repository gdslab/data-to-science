"""Checks and query fragments shared by more than one CRUD module."""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import ColumnElement, and_, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied
from app.models.data_product_view import DataProductView
from app.models.enums.project_type import ProjectType
from app.models.flight import Flight
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.schemas.project_member import Role

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

    Only a live project blocks deactivation. update_project_visibility only
    unpublishes active projects, so an already inactive project that still
    carries the published flag would otherwise be impossible to unpublish and
    impossible to finish deactivating.

    Args:
        db (Session): Database session.
        project_id (UUID): ID of the project being deactivated.

    Raises:
        PermissionDenied: If the project is published.
    """
    published_query = select(Project.is_published).where(
        Project.id == project_id, Project.is_active
    )
    with db as session:
        is_published = session.scalar(published_query)

    if is_published:
        raise PermissionDenied(PUBLISHED_PROJECT_DETAIL)


def raise_if_owning_project_published(
    db: Session, model: Any, item_id: UUID, item_type: str
) -> None:
    """Refuse to deactivate a record inside a published project.

    Called by the public deactivate methods rather than by their callers, so a
    record is protected no matter what reaches it: an endpoint, a background
    task, or a script. A record with no project left to check is allowed
    through, and the deactivate method reports it missing as it would have
    anyway. Cascades call the deactivate_unguarded methods, which skip this
    check because the operation's entry point already made it.

    Only a live project blocks deactivation, for the reason given in
    raise_if_project_published.

    Args:
        db (Session): Database session.
        model (Any): Flight, DataProduct, or RawData model.
        item_id (UUID): ID of the record being deactivated.
        item_type (str): Type of record, used in the error message (e.g.,
            "flight").

    Raises:
        PermissionDenied: If the project the record belongs to is published.
    """
    published_query = (
        select(Project.is_published)
        .join(Flight, Flight.project_id == Project.id)
        .where(Project.is_active)
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


def owner_membership_filter() -> ColumnElement[bool]:
    """ProjectMember rows that grant the OWNER role on a project.

    Ownership is role-based, not the single Project.owner_id creator: the
    creator is added as a ProjectMember with role=OWNER, and other members can
    be promoted to OWNER. Every owner-credited metric uses this same rule.
    """
    return and_(
        ProjectMember.role == Role.OWNER,
        ProjectMember.project_type == ProjectType.PROJECT,
    )


def owned_project_ids(user_id: UUID):
    """Project IDs where user_id holds the OWNER role."""
    return select(ProjectMember.project_uuid).where(
        ProjectMember.member_id == user_id, owner_membership_filter()
    )


def project_owners_subquery():
    """(member_id, project_uuid) for every owner of every project."""
    return (
        select(ProjectMember.member_id, ProjectMember.project_uuid)
        .where(owner_membership_filter())
        .subquery()
    )


def not_self_view(owner_id: UUID | ColumnElement[Any]) -> ColumnElement[bool]:
    """Views by anyone other than owner_id; anonymous session views always count."""
    return or_(DataProductView.user_id.is_(None), DataProductView.user_id != owner_id)
