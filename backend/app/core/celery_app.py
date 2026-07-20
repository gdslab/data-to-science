from celery import Celery  # type: ignore
from celery.signals import after_setup_logger  # type: ignore

from app.core.logging import suppress_noisy_loggers

celery_app = Celery("worker")  # Check backend.env for broker env settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Limit workers to fetching one task at a time
celery_app.conf.worker_prefetch_multiplier = 1

# Autodiscover tasks
celery_app.autodiscover_tasks(["app.tasks"], related_name="tasks")


@after_setup_logger.connect
def _suppress_noisy_loggers(**kwargs) -> None:
    """Apply our third-party log-level overrides after celery configures its
    own logging, so celery's setup doesn't reset them back to the defaults.
    """
    suppress_noisy_loggers()
