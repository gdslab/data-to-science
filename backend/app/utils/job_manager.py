import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import UUID

from app import crud
from app.api.deps import get_db
from app.models import Job as JobModel
from app.schemas.job import JobCreate, JobUpdate, State, Status

logger = logging.getLogger(__name__)


class JobManager:
    def __init__(
        self,
        data_product_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None,
        job_name: Optional[str] = None,
        raw_data_id: Optional[UUID] = None,
    ) -> None:
        """Initialize the JobManager instance.

        Args:
            data_product_id (Optional[UUID], optional): ID of the associated data product.
            job_id (Optional[UUID], optional): Existing jbo ID to lookup. If provided, the job will be retrieved from the DB.
            job_name (Optional[str], optional): Name of the job. If not provided, defaults to 'default-job'.
            raw_data_id (Optional[UUID], optional): ID of the raw data associated with the job.

        Raises:
            ValueError: Raised if a job_id is provided but the job is not found in the database.
        """
        self.data_product_id = data_product_id
        self.raw_data_id = raw_data_id

        # Retrieve a database session from the dependency injection.
        self.db = next(get_db())

        self.job_id = job_id
        self.job_name = job_name

        if self.job_id:
            # If a job_id is provided, try to retrieve the corresponding job from the database.
            self.job = self.get()
            if not self.job:
                # If no job is found, raise an error to prevent further operations on a non-existent job.
                raise ValueError(f"Job with ID {self.job_id} not found.")
        else:
            # If no job_id is provided, create a new job record in the database.
            self.job = self.create()

    def create(self) -> Optional[JobModel]:
        """Create a new job in the database.

        Returns:
            Optional[JobModel]: Job object created in the database or None.
        """
        # Use provided job_name or default to 'default-job'
        job_name = self.job_name or "default-job"

        job_obj_in = JobCreate(
            name=job_name,
            start_time=datetime.now(tz=timezone.utc),
            state=State.PENDING,
            status=Status.WAITING,
        )

        if self.data_product_id:
            job_obj_in.data_product_id = self.data_product_id

        if self.raw_data_id:
            job_obj_in.raw_data_id = self.raw_data_id

        # Create the job using the CRUD utility and update the job_id attribute
        job = crud.job.create(self.db, obj_in=job_obj_in)
        self.job_id = job.id

        logger.info(f"Job {job.id} created.")

        return job

    def get(self) -> Optional[JobModel]:
        """Retrieve a job from the database using the job_id.

        Returns:
            Optional[JobModel]: Job object returned from the database or None.
        """
        job_id = self.job_id
        if not job_id:
            logger.error("Job ID not provided.")
            return None

        # Retrieve the job record using the CRUD utility
        job = crud.job.get(self.db, id=job_id)
        if not job:
            logger.error(f"Job with ID {job_id} not found.")
            return None

        return job

    def start(self) -> None:
        """Mark the job as started by updating its status and state."""
        # Update the job's status to INPROGRESS, which updates its state to STARTED
        self.update(status=Status.INPROGRESS)

        logger.info(f"Job {self.job_id} started.")

    def update(self, status: Status, extra: Optional[Dict] = None) -> None:
        """Update the job's state and status in the database.

        Args:
            status (Status): The new status to set.
            extra (Optional[Dict], optional): Additional information to include in the update. Defaults to None.
        """
        job_db_obj = self.job
        if not job_db_obj:
            logger.error(f"Job with ID {self.job_id} not found.")
            return

        if status == Status.INPROGRESS:
            # If the job is in progress, update the state to STARTED
            job_obj_in = JobUpdate(
                state=State.STARTED,
                status=status,
            )
        else:
            # For any other status, assume the job is completed and set the end_time
            job_obj_in = JobUpdate(
                state=State.COMPLETED,
                status=status,
                end_time=datetime.now(tz=timezone.utc),
            )

        if extra:
            # Include any extra details provided
            job_obj_in.extra = extra

        # Update the job record in the database
        crud.job.update(self.db, db_obj=job_db_obj, obj_in=job_obj_in)

        # Refresh the local job object to reflect the latest database state
        self.job = self.get()

        logger.info(f"Job {self.job_id} updated with status {status}.")
