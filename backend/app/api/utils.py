import os
import uuid

from geojson_pydantic import Feature

from app.core.config import settings
from app.utils.MapMaker import MapMaker


def create_project_field_preview(project_id: uuid.UUID, features: list[Feature]) -> str:
    """Create preview image of project field boundary.

    Args:
        project_id (uuid.UUID4): Project ID.
        features (list[Feature]): GeoJSON features that represent field boundary.

    Returns:
        str: Path to generated preview image.
    """
    # Set output path for preview map
    if os.environ.get("RUNNING_TESTS") == "1":
        project_map_path = f"{settings.TEST_STATIC_DIR}/projects/{project_id}"
    else:
        project_map_path = f"{settings.STATIC_DIR}/projects/{project_id}"
    # Create project directory if needed, remove any existing preview maps
    if not os.path.exists(project_map_path):
        os.makedirs(project_map_path)
    if os.path.exists(os.path.join(project_map_path, "preview_map.png")):
        os.remove(os.path.join(project_map_path, "preview_map.png"))
    # Generate project map with provided coordinates
    project_map = MapMaker(features=features, outpath=project_map_path)
    project_map.save()
    return project_map.preview_img


def create_vector_layer_preview(
    project_id: uuid.UUID, layer_id: str, features: list[Feature]
) -> str:
    """Create preview image of vector layer.

    Args:
        project_id (uuid.UUID4): Project ID.
        layer_id (str): Unique layer ID for FeatureCollection.
        features (list[Feature]): GeoJSON features that represent vector layer shapes.

    Returns:
        str: Path to generated preview image.
    """
    # Set output path for preview image
    if os.environ.get("RUNNING_TESTS") == "1":
        preview_path = (
            f"{settings.TEST_STATIC_DIR}/projects/{project_id}/vector/{layer_id}"
        )
    else:
        preview_path = f"{settings.STATIC_DIR}/projects/{project_id}/vector/{layer_id}"
    # Create vector directory if needed, remove any existing preview for this layer
    if not os.path.exists(preview_path):
        os.makedirs(preview_path)
    # Full path to preview image
    preview_img = os.path.join(preview_path, "preview.png")
    # Skip creating preview image if one already exists
    if not os.path.exists(os.path.join(preview_path, "preview.png")):
        # Generate preview with provided coordinates
        vector_layer_preview = MapMaker(features=features, outpath=preview_path)
        vector_layer_preview.save(outname="preview.png")

    return preview_img


def is_valid_uuid(id: str) -> bool:
    """Checks if the provided ID is a version 4 UUID.

    Args:
        id (str): ID to check.

    Returns:
        bool: True if ID is valid ver. 4 UUID, False otherwise.
    """
    try:
        uuid.UUID(id, version=4)
        return True
    except ValueError:
        return False
