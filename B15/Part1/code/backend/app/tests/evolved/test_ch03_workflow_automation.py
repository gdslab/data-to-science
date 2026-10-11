"""Unit tests for Change 3 (CH03): Automated Experiment Workflow Pipeline."""

import os
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from case_study.Part2.code.evolved.app.workflow.base import (
    WorkflowContext,
    WorkflowListener,
    WorkflowStatus,
    WorkflowStep,
)
from case_study.Part2.code.evolved.app.workflow.pipeline import (
    ExperimentWorkflowPipeline,
)
from case_study.Part2.code.evolved.app.workflow.steps import (
    IngestionValidationStep,
    PhotogrammetryDispatchStep,
    PublishNotificationStep,
    SpatialMetadataExtractionStep,
    STACCatalogGenerationStep,
)


class MockWorkflowObserver(WorkflowListener):
    def __init__(self):
        self.started_steps = []
        self.completed_steps = []
        self.failed_steps = []

    def on_step_started(self, step_name: str, context: WorkflowContext) -> None:
        self.started_steps.append(step_name)

    def on_step_completed(self, step_name: str, context: WorkflowContext) -> None:
        self.completed_steps.append(step_name)

    def on_step_failed(self, step_name: str, context: WorkflowContext, error: Exception) -> None:
        self.failed_steps.append(step_name)


def test_pipeline_end_to_end_success():
    """Verify sequential execution of all pipeline steps and observer notification."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        archive_path = os.path.join(tmp_dir, "flight_imagery.zip")
        with open(archive_path, "wb") as f:
            f.write(b"SAMPLE_UAV_RAW_IMAGES_ZIP_ARCHIVE")

        ctx = WorkflowContext(
            flight_id=uuid.uuid4(),
            input_archive_path=archive_path,
            output_directory=tmp_dir,
            photogrammetry_backend="odm",
        )

        pipeline = ExperimentWorkflowPipeline()
        observer = MockWorkflowObserver()
        pipeline.register_listener(observer)

        status = pipeline.execute(ctx)

        assert status == WorkflowStatus.COMPLETED
        assert len(observer.completed_steps) == 5
        assert "IngestionValidation" in observer.completed_steps
        assert "PhotogrammetryDispatch" in observer.completed_steps
        assert "SpatialMetadataExtraction" in observer.completed_steps
        assert "STACCatalogGeneration" in observer.completed_steps
        assert "PublishNotification" in observer.completed_steps

        # Check artifact properties
        assert ctx.spatial_metadata["crs"]["epsg"] == 4326
        assert ctx.stac_catalog["type"] == "Feature"
        assert len(ctx.created_product_ids) == 1


def test_pipeline_failure_and_rollback():
    """Verify that a failing step halts pipeline and triggers compensating rollback."""
    class FailingStep(WorkflowStep):
        def __init__(self):
            super().__init__("FailingStep")

        def execute(self, context: WorkflowContext) -> bool:
            raise RuntimeError("Simulated processing failure")

        def rollback(self, context: WorkflowContext) -> None:
            context.log("FailingStep rollback")

    with tempfile.TemporaryDirectory() as tmp_dir:
        archive_path = os.path.join(tmp_dir, "flight_imagery.zip")
        with open(archive_path, "wb") as f:
            f.write(b"SAMPLE_DATA")

        ctx = WorkflowContext(
            flight_id=uuid.uuid4(),
            input_archive_path=archive_path,
            output_directory=tmp_dir,
        )

        pipeline = ExperimentWorkflowPipeline(steps=[
            IngestionValidationStep(),
            PhotogrammetryDispatchStep(),
            FailingStep(),
            PublishNotificationStep(),
        ])

        observer = MockWorkflowObserver()
        pipeline.register_listener(observer)

        status = pipeline.execute(ctx)

        assert status == WorkflowStatus.FAILED
        assert "FailingStep" in observer.failed_steps
        assert "PublishNotification" not in observer.completed_steps
        assert any("Initiating compensating transaction rollback" in log for log in ctx.execution_logs)
