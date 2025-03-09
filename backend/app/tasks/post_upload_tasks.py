from pathlib import Path

from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.tasks.job_manager import JobManager, Status
from app.utils import gen_preview_from_pointcloud


logger = get_task_logger(__name__)


@celery_app.task(name="generate_point_cloud_preview_task")
def generate_point_cloud_preview(in_las_filepath: str) -> None:
    """Celery task for creating a preview image for a point cloud.

    Args:
        in_las_filepath (str): Path to point cloud.
    """
    # create preview image with uploaded point cloud
    try:
        job = JobManager(job_name="point-cloud-preview")
        job.start()
        in_las = Path(in_las_filepath)
        if in_las.name.endswith(".copc.laz"):
            preview_out_path = in_las.parents[0] / in_las.name.replace(
                ".copc.laz", ".png"
            )
        else:
            preview_out_path = in_las.parents[0] / in_las.with_suffix(".png").name
        gen_preview_from_pointcloud.create_preview_image(
            input_las_path=in_las,
            preview_out_path=preview_out_path,
        )
    except Exception:
        logger.exception("Unable to generate preview image for uploaded point cloud")
        job.update(status=Status.FAILED)
        # if this file is present the preview image generation will be skipped next time
        with open(Path(in_las).parent / "preview_failed", "w"):
            pass

    job.update(status=Status.SUCCESS)
