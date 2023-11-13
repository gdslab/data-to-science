import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logger
from app.utils.ProtectedStaticFiles import ProtectedStaticFiles


app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)
cog = TilerFactory()

setup_logger()
logger = logging.getLogger(__name__)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])

app.mount("/static", ProtectedStaticFiles(directory=settings.UPLOAD_DIR), name="static")
app.mount("/potree", StaticFiles(directory=settings.POTREE_DIR), name="potree")

add_exception_handlers(app, DEFAULT_STATUS_CODES)
