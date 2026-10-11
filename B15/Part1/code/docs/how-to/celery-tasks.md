# Work with Celery Tasks

D2S uses [Celery](https://docs.celeryq.dev/) for asynchronous background processing. This guide covers adding and modifying tasks.

## Existing task modules

Task definitions are in `backend/app/tasks/`:

| Module | Purpose |
|--------|---------|
| `upload_tasks.py` | File processing (COG conversion, point cloud processing, vector formats) |
| `raw_image_processing_tasks.py` | Raw image processing pipeline |
| `stac_tasks.py` | STAC catalog operations |
| `toolbox_tasks.py` | Analytics tools (NDVI, CHM, zonal statistics) |
| `post_upload_tasks.py` | Post-upload operations |
| `admin_tasks.py` | Administrative operations |

## Adding a new task

1. Define the task in the appropriate module (or create a new one in `backend/app/tasks/`):

    ```python
    from app.core.celery_app import celery_app

    @celery_app.task
    def your_task(arg1, arg2):
        # Task logic here
        ...
    ```

2. Dispatch the task from an API endpoint or another task:

    ```python
    from app.tasks.your_module import your_task

    your_task.delay(arg1, arg2)
    ```

## Monitoring tasks

Task progress is tracked in the database and polled by the frontend. Long-running tasks update their status records so clients can display progress indicators.
