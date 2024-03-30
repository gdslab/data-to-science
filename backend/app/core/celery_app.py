from celery import Celery

celery_app = Celery("worker", broker="amqp://guest@queue//")
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
