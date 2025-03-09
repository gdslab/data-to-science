from celery.schedules import crontab
from celery.utils.log import get_task_logger

from app import crud
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.core.config import settings
from app.crud.crud_admin import get_disk_usage
from app.schemas.disk_usage_stats import DiskUsageStatsCreate
from app.utils.job_manager import JobManager, Status

logger = get_task_logger(__name__)


# Schedule periodic tasks here
celery_app.conf.beat_schedule = {
    "calculate-disk-usage": {
        "task": "calculate_disk_usage_task",
        "schedule": crontab(hour=6, minute=5),
        "args": (),
    },
}


@celery_app.task(name="calculate_disk_usage_task")
def calculate_disk_usage() -> None:
    # Create job to track progress
    job = JobManager(job_name="calculate-disk-usage")
    job.start()

    # Get database session
    db = next(get_db())

    # Get disk usage stats
    try:
        total, used, free = get_disk_usage(settings.STATIC_DIR)
    except Exception:
        logger.exception("Unable to calculate disk usage")
        job.update(status=Status.FAILED)
        return None

    try:
        # Create disk usage stats record
        obj_in = DiskUsageStatsCreate(disk_free=free, disk_total=total, disk_used=used)
        disk_usage_stats = crud.disk_usage_stats.create(db, obj_in=obj_in)
        assert disk_usage_stats
    except Exception:
        logger.exception("Unable to create disk usage record")
        job.update(status=Status.FAILED)
        return None

    # Update job status
    job.update(status=Status.SUCCESS)
