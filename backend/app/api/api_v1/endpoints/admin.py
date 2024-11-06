import logging
import os
from typing import Any, cast, Dict, List, Union
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session


from app import crud, models, schemas
from app.api import deps
from app.api.utils import get_static_dir, get_user_name_and_email
from app.crud.crud_admin import get_site_statistics, get_static_directory_size

router = APIRouter()

logger = logging.getLogger("__name__")


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
    """
    projects = crud.project.get_multi(db, limit=10000)

    static_dir = get_static_dir()

    result: Dict[str, Dict[str, Union[int, str]]] = {}

    for project in projects:
        user_id = str(project.owner_id)
        project_storage = get_static_directory_size(
            os.path.join(static_dir, "projects", str(project.id))
        )
        if user_id in result:
            if isinstance(result[user_id]["total_projects"], int):
                result[user_id]["total_projects"] = (
                    cast(int, result[user_id]["total_projects"]) + 1
                )

            if isinstance(result[user_id]["total_active_projects"], int):
                result[user_id]["total_active_projects"] = (
                    (cast(int, result[user_id]["total_active_projects"]) + 1)
                    if project.is_active
                    else cast(int, result[user_id]["total_active_projects"])
                )

            if isinstance(result[user_id]["total_storage"], int):
                result[user_id]["total_storage"] = (
                    cast(int, result[user_id]["total_storage"]) + project_storage
                )

            if isinstance(result[user_id]["total_active_storage"], int):
                result[user_id]["total_active_storage"] = (
                    (
                        cast(int, result[user_id]["total_active_storage"])
                        + project_storage
                    )
                    if project.is_active
                    else cast(int, result[user_id]["total_active_storage"])
                )
        else:
            result[user_id] = {
                "user": get_user_name_and_email(db, project.owner_id),
                "total_projects": 1,
                "total_active_projects": 1 if project.is_active else 0,
                "total_storage": project_storage,
                "total_active_storage": project_storage if project.is_active else 0,
            }

    project_statistics = [
        {"id": user_id, **details} for user_id, details in result.items()
    ]

    return project_statistics


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
