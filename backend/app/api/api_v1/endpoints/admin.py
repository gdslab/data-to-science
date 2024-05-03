import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session


from app import models, schemas
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
