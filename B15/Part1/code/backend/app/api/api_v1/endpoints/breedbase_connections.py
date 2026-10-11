import ipaddress
import json
import socket
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()
study_router = APIRouter()
oauth_router = APIRouter()
proxy_router = APIRouter()


class BrAPIProxyRequest(BaseModel):
    url: HttpUrl
    method: Literal["GET", "POST"] = "GET"
    body: Optional[Dict[str, Any]] = None
    brapi_token: Optional[str] = None


@router.post(
    "", response_model=schemas.BreedbaseConnection, status_code=status.HTTP_201_CREATED
)
def create_breedbase_connection(
    project_id: UUID,
    breedbase_connection_in: schemas.BreedbaseConnectionCreate,
    project: models.Project = Depends(deps.can_read_write_project_with_jwt_or_api_key),
    current_user: models.User = Depends(
        deps.get_current_approved_user_by_jwt_or_api_key
    ),
    db: Session = Depends(deps.get_db),
) -> Any:
    breedbase_connection = crud.breedbase_connection.create_with_project(
        db, obj_in=breedbase_connection_in, project_id=project.id
    )
    return breedbase_connection


@router.get("/{breedbase_connection_id}", response_model=schemas.BreedbaseConnection)
def read_breedbase_connection(
    breedbase_connection_id: UUID,
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_project),
) -> Any:
    breedbase_connection = crud.breedbase_connection.get(db, id=breedbase_connection_id)
    return breedbase_connection


@study_router.get("/{study_id}", response_model=List[schemas.BreedbaseConnection])
def read_breedbase_connection_by_study_id(
    study_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(
        deps.get_current_approved_user_by_jwt_or_api_key
    ),
) -> Any:
    breedbase_connections = crud.breedbase_connection.get_by_study_id(
        db, study_id=study_id, user_id=current_user.id
    )
    return breedbase_connections


@router.get("", response_model=List[schemas.BreedbaseConnection])
def read_breedbase_connections(
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_project_with_jwt_or_api_key),
) -> Any:
    breedbase_connections = crud.breedbase_connection.get_multi_by_project_id(
        db, project_id=project.id
    )
    return breedbase_connections


@router.put("/{breedbase_connection_id}", response_model=schemas.BreedbaseConnection)
def update_breedbase_connection(
    breedbase_connection_id: UUID,
    breedbase_connection_in: schemas.BreedbaseConnectionUpdate,
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_write_project_with_jwt_or_api_key),
) -> Any:
    # Get breedbase connection
    breedbase_connection = crud.breedbase_connection.get(db, id=breedbase_connection_id)
    if not breedbase_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Breedbase connection not found",
        )

    # Update breedbase connection
    breedbase_connection_updated = crud.breedbase_connection.update(
        db, db_obj=breedbase_connection, obj_in=breedbase_connection_in
    )
    return breedbase_connection_updated


@router.delete("/{breedbase_connection_id}", response_model=schemas.BreedbaseConnection)
def delete_breedbase_connection(
    breedbase_connection_id: UUID,
    db: Session = Depends(deps.get_db),
    project: models.Project = Depends(deps.can_read_write_project_with_jwt_or_api_key),
) -> Any:
    # Get breedbase connection
    breedbase_connection = crud.breedbase_connection.get(db, id=breedbase_connection_id)
    if not breedbase_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Breedbase connection not found",
        )

    # Delete breedbase connection
    crud.breedbase_connection.remove(db, id=breedbase_connection_id)
    return breedbase_connection


@oauth_router.get("/callback", response_class=HTMLResponse)
def oauth_callback(
    status_code: Optional[str] = Query(None, alias="status"),
    access_token: Optional[str] = Query(None),
) -> HTMLResponse:
    """Handle OAuth callback from BreedBase. Relays the token to the opener
    window via postMessage and closes the popup."""
    if status_code == "200" and access_token:
        payload_json = json.dumps(
            {
                "type": "breedbase-oauth-callback",
                "status": "200",
                "accessToken": access_token,
            }
        )
    else:
        payload_json = json.dumps(
            {
                "type": "breedbase-oauth-callback",
                "status": "error",
                "error": "Authorization failed or was denied.",
            }
        )

    html = f"""<!DOCTYPE html>
<html>
<head><title>BreedBase Authorization</title></head>
<body>
<p>Authorization complete. You may close this window.</p>
<script>
  if (window.opener) {{
    window.opener.postMessage({payload_json}, window.location.origin);
    window.close();
  }}
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


def _validate_proxy_url(url: str) -> None:
    """Validate that a proxy URL is safe to request (SSRF protection)."""
    parsed = urlparse(url)

    # Require /brapi/ in the path
    if "/brapi/" not in (parsed.path or ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proxy URL must contain a /brapi/ path segment.",
        )

    # Validate hostname exists
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL: no hostname.",
        )

    # Check hostname allowlist (if configured)
    allowed_hosts = settings.BREEDBASE_ALLOWED_HOSTS
    if allowed_hosts:
        allowed = {h.strip().lower() for h in allowed_hosts.split(",") if h.strip()}
        if hostname.lower() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Host is not in the allowed BreedBase hosts list.",
            )

    # Resolve hostname and reject private/reserved IPs
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not resolve hostname.",
        )

    for result in addr_info:
        ip = ipaddress.ip_address(result[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Proxy requests to private/internal addresses are not allowed.",
            )


@proxy_router.post("/proxy")
async def brapi_proxy(
    request: BrAPIProxyRequest,
    current_user: models.User = Depends(
        deps.get_current_approved_user_by_jwt_or_api_key
    ),
) -> JSONResponse:
    """Proxy a BrAPI request to an external BreedBase server."""
    _validate_proxy_url(str(request.url))

    headers = {"Content-Type": "application/json"}
    if request.brapi_token:
        headers["Authorization"] = f"Bearer {request.brapi_token}"

    try:
        async with httpx.AsyncClient() as client:
            if request.method.upper() == "POST":
                response = await client.post(
                    str(request.url),
                    json=request.body,
                    headers=headers,
                    timeout=30.0,
                )
            else:
                response = await client.get(
                    str(request.url),
                    headers=headers,
                    timeout=30.0,
                )
    except httpx.ConnectTimeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Connection to BrAPI server timed out.",
        )
    except httpx.ReadTimeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="BrAPI server took too long to respond.",
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not connect to BrAPI server.",
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error communicating with BrAPI server.",
        )

    try:
        content = response.json()
    except Exception:
        content = {"error": "Invalid or empty response from BrAPI server."}

    return JSONResponse(content=content, status_code=response.status_code)
