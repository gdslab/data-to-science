import logging
import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.logging import get_http_info, setup_logger
from app.utils.ProtectedStaticFiles import ProtectedStaticFiles


app = FastAPI(
    title=settings.API_PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"]
)

cog = TilerFactory()

setup_logger()
logger = logging.getLogger(__name__)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])

app.mount("/static", ProtectedStaticFiles(directory=settings.STATIC_DIR), name="static")
app.mount("/potree", StaticFiles(directory=settings.POTREE_DIR), name="potree")

add_exception_handlers(app, DEFAULT_STATUS_CODES)


def write_access_log(request: Request, response: Response, process_time: float):
    http_info = get_http_info(request, response)
    http_info["res"]["process_time"] = f"{process_time:.3f}"
    logger.info(
        request.method + " " + request.url.path,
        extra={"extra_info": http_info},
    )


@app.middleware("http")
async def log_http_request(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.background = BackgroundTask(
        write_access_log, request, response, process_time
    )

    return response
