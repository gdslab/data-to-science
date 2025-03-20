from celery import Celery  # type: ignore

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
