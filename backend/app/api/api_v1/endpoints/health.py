from typing import Any

from fastapi import APIRouter, status

from app.utils.titiler import titiler_status

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
def check_health() -> Any:
    return {
        "status": "healthy",
        "titiler": {
            "version": titiler_status.version,
            "compatible": titiler_status.compatible,
        },
    }
