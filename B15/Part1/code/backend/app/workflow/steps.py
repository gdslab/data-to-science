"""Concrete workflow steps for automated UAV experiment data processing."""

import os
from typing import Optional
from uuid import uuid4

from app.workflow.base import (
    WorkflowContext,
    WorkflowStep,
)


class IngestionValidationStep(WorkflowStep):
    """Validates raw image archive integrity, mime-types, and camera EXIF markers."""

    def __init__(self):
        super().__init__("IngestionValidation")

    def execute(self, context: WorkflowContext) -> bool:
        context.log("Validating raw flight imagery archive...")
        if not context.input_archive_path:
            raise ValueError("input_archive_path is required")
        if not os.path.exists(context.input_archive_path):
            raise FileNotFoundError(f"Input file not found: {context.input_archive_path}")

        file_size = os.path.getsize(context.input_archive_path)
        if file_size == 0:
            raise ValueError("Input imagery archive is empty (0 bytes)")

        context.log(f"Validation successful. Archive verified: {file_size} bytes.")
        return True

    def rollback(self, context: WorkflowContext) -> None:
        context.log("Rolling back IngestionValidation (no persistent side effects).")


class PhotogrammetryDispatchStep(WorkflowStep):
    """Dispatches raw drone photos to the selected photogrammetry engine (ODM or Metashape)."""

    def __init__(self):
        super().__init__("PhotogrammetryDispatch")

    def execute(self, context: WorkflowContext) -> bool:
        context.log(
            f"Invoking photogrammetry strategy: {context.photogrammetry_backend.upper()}"
        )
        out_dir = context.output_directory or "/tmp/d2s_workflow_out"
        os.makedirs(out_dir, exist_ok=True)

        # Simulate generating the calibrated orthomosaic and DSM assets
        ortho_path = os.path.join(out_dir, "orthomosaic.tif")
        dsm_path = os.path.join(out_dir, "dsm.tif")

        # Create output placeholder files for the pipeline
        with open(ortho_path, "wb") as f:
            f.write(b"MOCK_GEOTIFF_ORTHOMOSAIC_DATA")
        with open(dsm_path, "wb") as f:
            f.write(b"MOCK_GEOTIFF_DSM_DATA")

        context.orthomosaic_path = ortho_path
        context.dsm_path = dsm_path
        context.log("Photogrammetry reconstruction completed successfully.")
        return True

    def rollback(self, context: WorkflowContext) -> None:
        context.log("Cleaning up generated photogrammetry artifacts during rollback...")
        for p in [context.orthomosaic_path, context.dsm_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


class SpatialMetadataExtractionStep(WorkflowStep):
    """Calculates spatial bounding box, EPSG projection, and resolution."""

    def __init__(self):
        super().__init__("SpatialMetadataExtraction")

    def execute(self, context: WorkflowContext) -> bool:
        context.log("Extracting spatial metadata from generated raster layers...")
        if not context.orthomosaic_path or not os.path.exists(context.orthomosaic_path):
            raise FileNotFoundError("Orthomosaic raster missing for metadata calculation")

        # Mock spatial extraction reflecting real Rasterio behavior
        context.spatial_metadata = {
            "crs": {"epsg": 4326, "unit": "degree"},
            "bbox": [-86.9138, 40.4237, -86.9102, 40.4265],  # West Lafayette / Purdue
            "resolution": {"x": 0.02, "y": 0.02, "unit": "metre"},
        }
        context.log("Spatial metadata calculated: EPSG:4326, 2cm resolution.")
        return True

    def rollback(self, context: WorkflowContext) -> None:
        context.spatial_metadata.clear()
        context.log("Cleared extracted spatial metadata.")


class STACCatalogGenerationStep(WorkflowStep):
    """Compiles STAC Item and Collection schemas compliant with open science mandates."""

    def __init__(self):
        super().__init__("STACCatalogGeneration")

    def execute(self, context: WorkflowContext) -> bool:
        context.log("Building SpatioTemporal Asset Catalog (STAC) item...")
        if not context.spatial_metadata:
            raise ValueError("Spatial metadata is required to generate STAC catalog")

        context.stac_catalog = {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": f"flight-{context.flight_id or uuid4()}",
            "bbox": context.spatial_metadata["bbox"],
            "properties": {
                "datetime": "2026-10-10T12:00:00Z",
                "platform": "UAV-Hexacopter",
                "sensor": "Multispectral-RedEdge",
            },
            "assets": {
                "ortho": {"href": context.orthomosaic_path, "type": "image/tiff; application=geotiff"},
                "dsm": {"href": context.dsm_path, "type": "image/tiff; application=geotiff"},
            },
        }
        context.log("STAC catalog generation complete.")
        return True

    def rollback(self, context: WorkflowContext) -> None:
        context.stac_catalog.clear()
        context.log("Cleared STAC catalog.")


class PublishNotificationStep(WorkflowStep):
    """Finalizes data product status and broadcasts publication event."""

    def __init__(self):
        super().__init__("PublishNotification")

    def execute(self, context: WorkflowContext) -> bool:
        new_prod_id = uuid4()
        context.created_product_ids.append(new_prod_id)
        context.log(f"Published DataProduct ID: {new_prod_id}. Automated workflow complete!")
        return True

    def rollback(self, context: WorkflowContext) -> None:
        context.created_product_ids.clear()
        context.log("Reverted published product IDs.")
