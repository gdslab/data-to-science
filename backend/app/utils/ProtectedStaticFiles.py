from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.utils.staticfiles import RangedStaticFiles

from app import crud
from app.api.deps import decode_jwt, can_read_project
from app.db.session import SessionLocal
from app.models.data_product import DataProduct
from app.schemas.api_key import APIKeyUpdate
from app.schemas.file_permission import FilePermissionUpdate


def verify_api_key_static_file_access(
    data_product: DataProduct, api_key: str, db: Session | None = None
):
    """Verify if user associated with API key is authorized to access the
    requested data product.

    Args:
        data_product (DataProduct): Data product that was requested.
        api_key (str): API key included in request.

    Returns:
        _type_: True if authorized to access, False otherwise.
    """
    # check if data product is active
    if not data_product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    # create database session
    if not db:
        db = SessionLocal()
    # get api key db obj
    api_key_obj = crud.api_key.get_by_api_key(db, api_key)

    if api_key_obj:
        # user associated with api key
        user = api_key_obj.owner
        # flight associated with data product
        flight = crud.flight.get(db, id=data_product.flight_id)
        # check if can read flight
        if can_read_project(db=db, project_id=flight.project_id, current_user=user):
            # update last accessed date and total requests
            api_key_in = APIKeyUpdate(
                last_used_at=datetime.utcnow(),
                total_requests=api_key_obj.total_requests + 1,
            )
            crud.api_key.update(db, db_obj=api_key_obj, obj_in=api_key_in)
            return True

    return False


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
    # check if access to color bar's data product is restricted or public
    if "colorbars" in request.url.path:
        try:
            request_path = Path(request.url.path)
            data_product_id = UUID(request_path.parents[1].name)
        except (IndexError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="data product not found"
            )
        file_permission = crud.file_permission.get_by_data_product(
            SessionLocal(), file_id=data_product_id
        )
        # public, return file
        if file_permission and file_permission.is_public:
            return

    # check if access to requested data product is restricted or public
    if "data_products" in request.url.path and "colorbars" not in request.url.path:
        try:
            request_path = Path(request.url.path.split("data_products")[1])
            data_product_id = UUID(request_path.parents[-2].name)
            data_product = crud.data_product.get(SessionLocal(), id=data_product_id)
        except (IndexError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="data product not found"
            )

        if "API_KEY" in request.query_params:
            api_key = request.query_params["API_KEY"]
            # check if owner of api key has access to requested static file
            if verify_api_key_static_file_access(data_product, api_key):
                return

        file_permission = crud.file_permission.get_by_data_product(
            SessionLocal(), file_id=data_product_id
        )
        # if file is deactivated return 404
        if file_permission and file_permission.file.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="data product not found",
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
        try:
            project = crud.project.get_user_project(
                SessionLocal(), user_id=user.id, project_id=project_id_uuid
            )
            assert project
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="unable to load project"
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
