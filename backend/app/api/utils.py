import os
import uuid

from app.core.config import settings
from app.utils.MapMaker import MapMaker


def create_project_field_preview(request, project_id, coordinates):
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
    project_map = MapMaker(coordinates[0], project_map_path)
    project_map.save()


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
