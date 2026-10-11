"""Experiment Workflow Pipeline orchestrator implementing Template Method & Observer patterns."""

import logging
from typing import List

from app.workflow.base import (
    WorkflowContext,
    WorkflowListener,
    WorkflowStatus,
    WorkflowStep,
)
from app.workflow.steps import (
    IngestionValidationStep,
    PhotogrammetryDispatchStep,
    PublishNotificationStep,
    SpatialMetadataExtractionStep,
    STACCatalogGenerationStep,
)

logger = logging.getLogger(__name__)


class ExperimentWorkflowPipeline:
    """Orchestrates an automated DAG pipeline for flight data processing.

    Implements:
    - Template Method / Command Pattern: Manages linear step execution and automated rollback.
    - Observer Pattern: Dispatches notifications to registered listeners on step events.
    """

    def __init__(self, steps: List[WorkflowStep] = None):
        self.steps: List[WorkflowStep] = steps or [
            IngestionValidationStep(),
            PhotogrammetryDispatchStep(),
            SpatialMetadataExtractionStep(),
            STACCatalogGenerationStep(),
            PublishNotificationStep(),
        ]
        self.listeners: List[WorkflowListener] = []
        self.executed_steps: List[WorkflowStep] = []

    def register_listener(self, listener: WorkflowListener) -> None:
        """Register an observer for workflow status notifications."""
        self.listeners.append(listener)

    def _notify_step_started(self, step_name: str, context: WorkflowContext) -> None:
        for listener in self.listeners:
            listener.on_step_started(step_name, context)

    def _notify_step_completed(self, step_name: str, context: WorkflowContext) -> None:
        for listener in self.listeners:
            listener.on_step_completed(step_name, context)

    def _notify_step_failed(
        self, step_name: str, context: WorkflowContext, error: Exception
    ) -> None:
        for listener in self.listeners:
            listener.on_step_failed(step_name, context, error)

    def execute(self, context: WorkflowContext) -> WorkflowStatus:
        """Execute all configured workflow steps sequentially with rollback on failure."""
        context.log(f"Starting Experiment Workflow Pipeline: {context.workflow_id}")
        self.executed_steps.clear()

        for step in self.steps:
            self._notify_step_started(step.name, context)
            try:
                success = step.execute(context)
                if not success:
                    raise RuntimeError(f"Step {step.name} returned failure status")
                self.executed_steps.append(step)
                self._notify_step_completed(step.name, context)
            except Exception as exc:
                context.error_message = str(exc)
                context.log(f"Step {step.name} failed: {exc}")
                self._notify_step_failed(step.name, context, exc)
                self._rollback(context)
                return WorkflowStatus.FAILED

        context.log("All pipeline steps completed successfully.")
        return WorkflowStatus.COMPLETED

    def _rollback(self, context: WorkflowContext) -> None:
        """Compensating rollback of all previously executed steps in reverse order."""
        context.log("Initiating compensating transaction rollback...")
        for step in reversed(self.executed_steps):
            try:
                step.rollback(context)
            except Exception as rollback_err:
                context.log(f"Error during rollback of {step.name}: {rollback_err}")
        context.log("Rollback completed.")
