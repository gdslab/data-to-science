import os

from app.core.config import settings
from app.utils.MapMaker import MapMaker


def create_project_field_preview(request, project_id, coordinates):
    # Set output path for preview map
    if request.client and request.client.host == "testclient":
        project_map_path = f"{settings.TEST_UPLOAD_DIR}/projects/{project_id}"
    else:
        project_map_path = f"{settings.UPLOAD_DIR}/projects/{project_id}"
    # Create project directory if needed, remove any existing preview maps
    if not os.path.exists(project_map_path):
        os.makedirs(project_map_path)
    if os.path.exists(os.path.join(project_map_path, "preview_map.png")):
        os.remove(os.path.join(project_map_path, "preview_map.png"))
    # Generate project map with provided coordinates
    project_map = MapMaker(coordinates[0], project_map_path)
    project_map.save()
