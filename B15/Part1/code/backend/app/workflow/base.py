"""Base interfaces and context for experiment workflow automation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass
class WorkflowContext:
    """Shared state container passed along the pipeline (Parameter Object Pattern)."""
    workflow_id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    flight_id: Optional[UUID] = None
    raw_data_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    photogrammetry_backend: str = "odm"  # "odm" or "metashape"
    
    # Artifact outputs and intermediate results
    input_archive_path: Optional[str] = None
    output_directory: Optional[str] = None
    orthomosaic_path: Optional[str] = None
    dsm_path: Optional[str] = None
    pointcloud_path: Optional[str] = None
    spatial_metadata: Dict[str, Any] = field(default_factory=dict)
    stac_catalog: Dict[str, Any] = field(default_factory=dict)
    created_product_ids: List[UUID] = field(default_factory=list)
    
    # Execution telemetry and logs
    execution_logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def log(self, message: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        self.execution_logs.append(f"[{timestamp}] {message}")


class WorkflowListener(ABC):
    """Observer interface for workflow telemetry and notifications."""

    @abstractmethod
    def on_step_started(self, step_name: str, context: WorkflowContext) -> None:
        pass

    @abstractmethod
    def on_step_completed(self, step_name: str, context: WorkflowContext) -> None:
        pass

    @abstractmethod
    def on_step_failed(self, step_name: str, context: WorkflowContext, error: Exception) -> None:
        pass


class WorkflowStep(ABC):
    """Template Method / Command interface for a modular pipeline task."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, context: WorkflowContext) -> bool:
        """Execute step logic. Return True on success, False or raise Exception on failure."""
        pass

    @abstractmethod
    def rollback(self, context: WorkflowContext) -> None:
        """Compensating transaction invoked if a subsequent step fails."""
        pass
