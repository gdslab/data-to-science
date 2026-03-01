import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional
from uuid import UUID

from fastapi import BackgroundTasks, Request, Response

from app import crud
from app.api.deps import get_db
from app.core.config import settings
from app.core.logging import get_http_info
from app.core.security import decode_token


logger = logging.getLogger(__name__)

# In-memory cache of user_id -> last time a DB activity update was scheduled.
# Prevents a background task (and DB connection) from being queued on every
# single request when the throttle window hasn't elapsed yet.
_activity_cache: dict[UUID, datetime] = {}

# How long (seconds) to wait for the sync DB work before giving up.
_ACTIVITY_TRACKING_TIMEOUT = 5.0


def write_access_log(request: Request, response: Response, process_time: float) -> None:
    """Write HTTP access log entry."""
    http_info = get_http_info(request, response)
    http_info["res"]["process_time"] = f"{process_time:.3f}"
    logger.info(
        request.method + " " + request.url.path,
        extra={"extra_info": http_info},
    )


def _sync_track_activity(user_id: UUID) -> None:
    """Synchronous DB work for updating user activity. Runs in a threadpool."""
    db_session = None
    try:
        db_session = next(get_db())
        user = crud.user.get_by_id(db_session, user_id=user_id)
        if user:
            crud.user.update_last_activity(
                db_session,
                user=user,
                throttle_minutes=settings.ACTIVITY_TRACKING_THROTTLE_MINUTES,
            )
    except Exception as e:
        logger.debug(f"Error tracking user activity: {e}")
    finally:
        if db_session:
            db_session.close()


async def track_activity_background(user_id: UUID) -> None:
    """
    Async background task that runs the sync DB activity update in a threadpool
    with a hard timeout so it can never block a Uvicorn worker from restarting.
    """
    try:
        await asyncio.wait_for(
            asyncio.to_thread(_sync_track_activity, user_id),
            timeout=_ACTIVITY_TRACKING_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.debug(
            f"Activity tracking timed out after {_ACTIVITY_TRACKING_TIMEOUT}s "
            f"for user {user_id}"
        )
    except Exception as e:
        logger.debug(f"Error tracking user activity: {e}")


def _should_track_activity(user_id: UUID) -> bool:
    """
    Return True only if enough time has passed since we last scheduled a DB
    update for this user. Uses an in-memory cache so we don't queue a task
    (and open a DB connection) on every single request.
    """
    now = datetime.now(timezone.utc)
    last = _activity_cache.get(user_id)
    throttle_seconds = settings.ACTIVITY_TRACKING_THROTTLE_MINUTES * 60
    if last is None or (now - last).total_seconds() > throttle_seconds:
        _activity_cache[user_id] = now
        return True
    return False


async def log_and_track_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Combined middleware to log HTTP requests and track user activity.

    Performs two functions:
    1. Logs HTTP requests with timing information.
    2. Tracks user activity for authenticated requests (with throttling).

    Both tasks run as background tasks after the response is sent to avoid
    interfering with request handling. Activity tracking is gated by an
    in-memory cache so a DB connection is only opened once per throttle window
    per user, regardless of request volume.
    """
    # Extract user info before processing request
    user_id_to_track: Optional[UUID] = None

    try:
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
    start_time = time.time()
    caught_exception: Optional[Exception] = None
    response: Optional[Response] = None
    try:
        response = await call_next(request)
    except Exception as exc:
        caught_exception = exc
        status_code = getattr(exc, "status_code", 500)
        response = Response(status_code=status_code)
    finally:
        process_time = time.time() - start_time
        if response is None:
            response = Response(status_code=500)

        # Merge any existing background tasks before appending ours
        existing_background = response.background
        if isinstance(existing_background, BackgroundTasks):
            tasks = existing_background
        else:
            tasks = BackgroundTasks()
            if existing_background:
                existing_tasks = getattr(existing_background, "tasks", None)
                if existing_tasks is not None:
                    tasks.tasks.extend(existing_tasks)
                else:
                    tasks.tasks.append(existing_background)

        tasks.add_task(write_access_log, request, response, process_time)

        # Only schedule a DB task if the in-memory throttle says it's time
        if (
            response.status_code < 400
            and user_id_to_track
            and _should_track_activity(user_id_to_track)
        ):
            tasks.add_task(track_activity_background, user_id_to_track)

        response.background = tasks

    if caught_exception:
        raise caught_exception

    return response
