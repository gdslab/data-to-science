import logging
import time
from typing import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask

from app.api.api_v1.api import api_router
from app.api.extras import extra_router
from app.core.config import settings
from app.core.logging import get_http_info, setup_logger
from app.utils.ProtectedStaticFiles import ProtectedStaticFiles


app = FastAPI(
    docs_url="/developer/api",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    redoc_url="/developer/docs",
    title=settings.API_PROJECT_NAME,
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"]
)

setup_logger()
logger = logging.getLogger(__name__)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(extra_router, tags=["extras"])

app.mount("/static", ProtectedStaticFiles(directory=settings.STATIC_DIR), name="static")
app.mount("/potree", StaticFiles(directory=settings.POTREE_DIR), name="potree")
app.mount(
    "/pc-gltf-viewer",
    StaticFiles(directory=settings.PC_GLTF_VIEWER_DIR, html=True),
    name="pc-gltf-viewer",
)


@app.get("/pc-gltf-viewer")
def pc_gltf_viewer_redirect():
    return RedirectResponse(url="/pc-gltf-viewer/")


@app.get("/pc-gltf-viewer/index.html")
def pc_gltf_viewer_index_redirect():
    return RedirectResponse(url="/pc-gltf-viewer/")


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.error(f"HTTPException", exc_info=exc)

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


def write_access_log(request: Request, response: Response, process_time: float) -> None:
    http_info = get_http_info(request, response)
    http_info["res"]["process_time"] = f"{process_time:.3f}"
    logger.info(
        request.method + " " + request.url.path,
        extra={"extra_info": http_info},
    )


@app.middleware("http")
async def log_http_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.background = BackgroundTask(
        write_access_log, request, response, process_time
    )

    return response
