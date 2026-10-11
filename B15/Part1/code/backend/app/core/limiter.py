from app.core.config import settings


def _key_func(request):
    # Read real client IP from forwarding headers set by the host-level nginx.
    # Falls back to request.client.host (uvicorn --proxy-headers) if not present.
    ip = (
        request.headers.get("X-Real-IP")
        or request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or None
    )
    if ip:
        return ip
    if request.client:
        return request.client.host
    return "unknown"


try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address  # noqa: F401 — kept for downstream use

    limiter = Limiter(
        key_func=_key_func,
        storage_uri=settings.RATE_LIMIT_STORAGE_URI,
        enabled=settings.RATE_LIMIT_ENABLED,
    )
except Exception:

    class _NoOpLimiter:
        """Fallback when slowapi is unavailable. Decorators become pass-throughs."""

        def limit(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    limiter = _NoOpLimiter()  # type: ignore[assignment]
