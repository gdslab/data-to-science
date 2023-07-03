import logging

from fastapi import FastAPI

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logger


app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

setup_logger()

logger = logging.getLogger(__name__)

app.include_router(api_router, prefix=settings.API_V1_STR)
