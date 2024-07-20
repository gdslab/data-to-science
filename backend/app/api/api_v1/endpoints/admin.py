import logging
from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session


from app import crud, models, schemas
from app.api import deps
from app.crud.crud_admin import get_site_statistics

router = APIRouter()

logger = logging.getLogger("__name__")


@router.get("/site_statistics", response_model=schemas.SiteStatistics)
def read_site_statistics(
    current_user: models.User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    stats = get_site_statistics(db)
    return stats


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
