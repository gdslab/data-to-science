import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.api.api_v1.api import api_router
from app.api.extras import extra_router
from app.core.config import settings
from app.core.logging import setup_logger
from app.middleware import log_and_track_middleware
from app.utils.ProtectedStaticFiles import ProtectedStaticFiles


app = FastAPI(
    docs_url="/developer/api",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    redoc_url="/developer/docs",
    title=settings.API_PROJECT_NAME,
)

if settings.ENABLE_OPENTELEMETRY:
    try:
        from app.telemetry import setup_tracing

        setup_tracing(service_name="d2s-api")
        FastAPIInstrumentor.instrument_app(app)  # route names, attrs
        app.add_middleware(OpenTelemetryMiddleware)  # full ASGI coverage
        print("OpenTelemetry tracing enabled")
    except Exception as e:
        print(f"Error setting up OpenTelemetry tracing: {e}")


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


# Register middleware
app.middleware("http")(log_and_track_middleware)
