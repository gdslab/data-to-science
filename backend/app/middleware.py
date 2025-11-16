import logging
import time
from typing import Awaitable, Callable
from uuid import UUID

from fastapi import Request, Response
from starlette.background import BackgroundTask

from app import crud
from app.api.deps import get_db
from app.core.config import settings
from app.core.logging import get_http_info
from app.core.security import decode_token


logger = logging.getLogger(__name__)


def write_access_log(request: Request, response: Response, process_time: float) -> None:
    """Write HTTP access log entry."""
    http_info = get_http_info(request, response)
    http_info["res"]["process_time"] = f"{process_time:.3f}"
    logger.info(
        request.method + " " + request.url.path,
        extra={"extra_info": http_info},
    )


async def log_http_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Middleware to log HTTP requests with timing information."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.background = BackgroundTask(
        write_access_log, request, response, process_time
    )

    return response


async def track_user_activity(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Middleware to track user activity for authenticated requests.

    Updates last_activity_at timestamp for users making authenticated requests,
    with throttling to prevent excessive database writes.

    Note: Activity tracking happens in a background task after the response
    is sent to avoid interfering with request handling and test sessions.
    """

    # Extract user info before processing request
    user_id_to_track = None

    try:
        # Check for JWT token in cookies
        access_token = request.cookies.get("access_token")
        if access_token and access_token.startswith("Bearer "):
            token = access_token.removeprefix("Bearer ").strip()
            try:
                payload = decode_token(token)
                if payload and payload.get("type") == "access":
                    user_id_str = payload.get("sub")
                    if user_id_str:
                        user_id_to_track = UUID(user_id_str)
            except Exception:
                pass  # Invalid token, skip activity tracking
    except Exception:
        pass

    # Process the request
    response = await call_next(request)

    # Schedule activity tracking as background task only for successful requests
    if response.status_code < 400 and user_id_to_track:
        async def track_activity():
            db_session = None
            try:
                db_session = next(get_db())
                user = crud.user.get_by_id(db_session, user_id=user_id_to_track)
                if user:
                    crud.user.update_last_activity(
                        db_session,
                        user=user,
                        throttle_minutes=settings.ACTIVITY_TRACKING_THROTTLE_MINUTES,
                    )
            except Exception as e:
                # Silently log errors during activity tracking
                logger.debug(f"Error tracking user activity: {e}")
            finally:
                if db_session:
                    db_session.close()

        # Add as background task so it runs after response is sent
        response.background = BackgroundTask(track_activity)

    return response
