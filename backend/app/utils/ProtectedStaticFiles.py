from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, Request, status

# from fastapi.staticfiles import StaticFiles
from app.utils.staticfiles import RangedStaticFiles

from app import crud
from app.api.deps import decode_jwt
from app.db.session import SessionLocal
from app.schemas.file_permission import FilePermissionUpdate


async def verify_static_file_access(request: Request) -> None:
    """
    Verify if requested static file has restricted or unrestricted access. If
    restricted, verify client requesting a static file has access to the project
    associated with the file.

    Args:
        request (Request): Client request for a static file

    Raises:
        HTTPException: Client not authenticated
        HTTPException: User associated with access token not found
        HTTPException: User does not have access to project
    """
    # check if access to requested file is restricted or public
    if "flights" in request.url.path:
        try:
            data_product_id = request.url.path.split("flights")[1].split("/")[-1][:-4]
            data_product_id_uuid = UUID(data_product_id)
        except (IndexError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="data product not found"
            )
        file_permission = crud.file_permission.get_by_filename(
            SessionLocal(), filename=str(data_product_id_uuid)
        )
        # public, return file
        if file_permission and file_permission.is_public:
            return
    # restricted access authorization
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    token_data = decode_jwt(access_token.split(" ")[1])
    if token_data.sub:
        user = crud.user.get(SessionLocal(), id=token_data.sub)
    if not token_data.sub or not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    if "projects" in request.url.path:
        try:
            project_id = request.url.path.split("/projects/")[1].split("/")[0]
            project_id_uuid = UUID(project_id)
        except (IndexError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="project not found"
            )
        project = crud.project.get_user_project(
            SessionLocal(), user_id=user.id, project_id=project_id_uuid
        )
        if project["response_code"] != status.HTTP_200_OK:
            raise HTTPException(
                status_code=project["response_code"], detail=project["message"]
            )
    elif "users" in request.url.path:
        try:
            user_id_in_url = request.url.path.split("/users/")[1].split("/")[0]
        except (IndexError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
            )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


class ProtectedStaticFiles(RangedStaticFiles):
    """Extend StatcFiles to include user access authorization."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def __call__(self, scope, receive, send) -> None:
        assert scope["type"] == "http"

        request = Request(scope, receive)
        await verify_static_file_access(request)
        await super().__call__(scope, receive, send)
