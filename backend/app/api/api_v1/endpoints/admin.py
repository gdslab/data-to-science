import logging
from typing import Annotated, Any, List, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session


from app import crud, models, schemas
from app.api import deps
from app.crud.crud_admin import get_project_data_usage, get_site_statistics

router = APIRouter()

logger = logging.getLogger("__name__")


@router.get("/users", response_model=list[schemas.UserAdmin])
def read_admin_users(
    q: Annotated[str | None, Query(max_length=50)] = None,
    current_user: models.User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Retrieve admin list of all users (including unapproved) with sensitive fields."""
    users = crud.user.get_multi_by_query(db, q=q, include_all=True)
    return users


@router.patch("/users/{user_id}/approval", response_model=schemas.UserAdmin)
def update_user_approval(
    user_id: UUID,
    approval_update: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Update user approval status. Requires superuser privileges."""
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = crud.user.update(db, db_obj=user, obj_in=approval_update)
    return updated_user


@router.get("/site_statistics", response_model=schemas.SiteStatistics)
def read_site_statistics(
    current_user: models.User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    stats = get_site_statistics(db)
    return stats


@router.get("/project_statistics", response_model=List[schemas.UserProjectStatistics])
def read_project_data_usage(
    current_user: models.User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Summarize user data usage by project ownership.

    Data usage is the SQL SUM of stored data product + raw data file sizes, not a
    filesystem walk.
    """
    return get_project_data_usage(db)


@router.get("/activity/summary", response_model=schemas.ActivitySummary)
def read_activity_summary(
    current_user: models.User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Current active-user counts and the signup -> first-project funnel."""
    return crud.metrics.get_activity_summary(db)


@router.get("/activity/trends", response_model=List[schemas.ActivityTrendPoint])
def read_activity_trends(
    days: Annotated[int, Query(ge=1, le=365)] = 90,
    current_user: models.User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Daily active-user time series (DAU/WAU/MAU) from recorded snapshots."""
    return crud.metrics.get_activity_trends(db, days=days)


@router.get("/activity/leaderboard", response_model=List[schemas.EngagementLeaderRow])
def read_engagement_leaderboard(
    metric: Literal[
        "projects", "flights", "data_products", "views", "likes", "storage"
    ] = "data_products",
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    current_user: models.User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Top users by content created or engagement received."""
    return crud.metrics.get_engagement_leaderboard(db, metric=metric, limit=limit)


@router.get("/extensions", response_model=List[schemas.Extension])
def read_extensions(
    current_user: models.User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    extensions = crud.extension.get_extensions(db)
    return extensions


@router.put("/extensions/team", response_model=schemas.TeamExtension)
def update_team_extension(
    team_extension_in: schemas.team_extension.TeamExtensionUpdate,
    current_user: models.User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    team_extension = crud.extension.create_or_update_team_extension(
        db, team_extension_in=team_extension_in
    )
    return team_extension


@router.put("/extensions/user", response_model=schemas.UserExtension)
def update_user_extension(
    user_extension_in: schemas.UserExtensionUpdate,
    current_user: models.User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    user_extension = crud.extension.create_or_update_user_extension(
        db, user_extension_in=user_extension_in
    )
    return user_extension
