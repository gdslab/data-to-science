import logging
from collections.abc import Generator
from typing import Any, Generator, Optional, Union
from uuid import UUID

from fastapi import BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.security import APIKeyHeader
from fastapi_mail import MessageSchema, MessageType
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.core.mail import fm
from app.crud.crud_flight import ReadFlight
from app.crud.crud_project import ReadProject
from app.db.session import SessionLocal
from app.api.utils import is_valid_api_key
from app.schemas.raw_data import MetashapeQueryParams, ODMQueryParams
from app.schemas.role import Role

logger = logging.getLogger("__name__")


header_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)
reusable_oauth2 = security.OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{settings.API_V1_STR}/auth/access-token"
)
# used for endpoints that can be authorized with api key or jwt token
reusable_oauth2_optional = security.OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{settings.API_V1_STR}/auth/access-token", auto_error=False
)


def get_db() -> Generator:
    """Create database session with lifespan of a single request."""
    db = SessionLocal()
    try:
        yield db
    except Exception as exception:
        db.rollback()
        exception_name = exception.__class__.__name__
        if exception_name == "JWTError" or exception_name == "JWSSignatureError":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Must sign in to access",
            )
        elif isinstance(exception, (HTTPException, RequestValidationError)):
            raise exception
        else:
            logger.exception("Uncaught error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error has occurred",
            )
    finally:
        db.close()


def send_email(
    subject: str,
    recipients: list[EmailStr],
    body: str,
    background_tasks: BackgroundTasks,
    cc: list[EmailStr] | None = None,
    reply_to: list[EmailStr] | None = None,
) -> None:
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        cc=cc or [],
        reply_to=reply_to or [],
        body=body,
        subtype=MessageType.html,
    )
    if settings.MAIL_ENABLED:
        background_tasks.add_task(fm.send_message, message)


def verify_user_account(current_user: Optional[models.User]) -> models.User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    if not crud.user.is_email_confirmed(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account requires email confirmation",
        )
    if not crud.user.is_approved(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account requires approval"
        )
    return current_user


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    # Validate token and get payload
    payload = security.validate_token_and_get_payload(token, "access")

    # Get user from payload
    user = security.get_user_from_token_payload(db, payload)

    return user


def get_current_approved_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    # verify user exists, email is confirmed, and account is approved
    # raises appropriate http exceptions when checks fail
    approved_user = verify_user_account(current_user)

    return approved_user


def get_current_approved_user_by_jwt_or_api_key(
    db: Session = Depends(get_db),
    api_key: str = Depends(header_scheme),
    token: str = Depends(reusable_oauth2_optional),
) -> models.User:
    user = None
    # must have api key or token
    if not api_key and not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # find user with jwt token
    if token and isinstance(token, str):
        # Validate token and get payload
        payload = security.validate_token_and_get_payload(token, "access")
        # Get user from payload
        user = security.get_user_from_token_payload(db, payload)

    # if user not found with jwt token, try api key
    if not user and api_key and isinstance(api_key, str):
        if not is_valid_api_key(api_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid API key provided",
            )
        user = crud.user.get_by_api_key(db, api_key=api_key)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    # verify user exists, email is confirmed, and account is approved
    # raises appropriate http exceptions when checks fail
    approved_user = verify_user_account(user)

    return approved_user


def get_optional_current_user(
    db: Session = Depends(get_db),
    api_key: str = Depends(header_scheme),
    token: str = Depends(reusable_oauth2_optional),
) -> Optional[models.User]:
    user = None

    # find user with jwt token
    if token and isinstance(token, str):
        try:
            # Validate token and get payload
            payload = security.validate_token_and_get_payload(token, "access")
            # Get user from payload
            user = security.get_user_from_token_payload(db, payload)
        except HTTPException:
            # Token validation failed, continue to try API key
            pass

    # if user not found with jwt token, try api key
    if not user and api_key and isinstance(api_key, str):
        if not is_valid_api_key(api_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid API key provided",
            )
        user = crud.user.get_by_api_key(db, api_key=api_key)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    # verify user exists, email is confirmed, and account is approved
    # returns None if checks fail
    try:
        approved_user = verify_user_account(user)
    except HTTPException:
        approved_user = None

    return approved_user


def get_current_admin_user(
    current_user: models.User = Depends(get_current_approved_user),
) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return current_user


def can_read_team(
    team_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> Optional[models.Team]:
    """Return team only if current user is a member of the team."""
    team = crud.team.get_team(
        db, user_id=current_user.id, team_id=team_id, permission="read"
    )
    if not team:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    return team


def can_read_write_team(
    team_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> Optional[models.Team]:
    """Return team only if current user is manager of the team."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    team = crud.team.get_team(
        db, user_id=current_user.id, team_id=team_id, permission="readwrite"
    )
    if not team:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    return team


def can_read_write_delete_indoor_project(
    indoor_project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> models.IndoorProject:
    """Return indoor project if current user is owner."""
    return crud.indoor_project.get_with_permission(
        db,
        indoor_project_id=indoor_project_id,
        user_id=current_user.id,
        required_permission=Role.OWNER,
    )


def can_read_write_indoor_project(
    indoor_project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> models.IndoorProject:
    """Return indoor project if current user is owner or manager."""
    return crud.indoor_project.get_with_permission(
        db,
        indoor_project_id=indoor_project_id,
        user_id=current_user.id,
        required_permission=Role.MANAGER,
    )


def can_read_indoor_project(
    indoor_project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> models.IndoorProject:
    """Return indoor project if current user is owner, manager, or viewer."""
    return crud.indoor_project.get_with_permission(
        db,
        indoor_project_id=indoor_project_id,
        user_id=current_user.id,
        required_permission=Role.VIEWER,
    )


def can_read_write_delete_team(
    team_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> Optional[models.Team]:
    """Return team only if current user is owner of the team."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    team = crud.team.get_team(
        db, user_id=current_user.id, team_id=team_id, permission="readwritedelete"
    )
    if not team:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    return team


def verify_resource_response(
    response: Union[dict, ReadProject, ReadFlight], resource_name: str
) -> Any:
    """Common verification logic for resource responses."""
    if response["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response["response_code"],
            detail=response["message"],
        )
    result = response["result"]
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource_name} not found"
        )
    return result


def can_read_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> schemas.Project:
    """Return project is current user is project owner, manager, or viewer."""
    project_response = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project_id, permission="r"
    )
    project = verify_resource_response(project_response, "Project")
    return project


def can_read_write_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> schemas.Project:
    """Return project if current user is project owner or manager."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    project_response = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project_id, permission="rw"
    )
    project = verify_resource_response(project_response, "Project")
    return project


def can_read_project_with_jwt_or_api_key(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user_by_jwt_or_api_key),
) -> schemas.Project:
    """Return project if current user is project owner, manager, or viewer."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    project_response = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project_id, permission="r"
    )
    project = verify_resource_response(project_response, "Project")
    return project


def can_read_write_project_with_jwt_or_api_key(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user_by_jwt_or_api_key),
) -> schemas.Project:
    """Return project if current user is project owner or manager."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    project_response = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project_id, permission="rw"
    )
    project = verify_resource_response(project_response, "Project")
    return project


def can_read_write_delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> schemas.Project:
    """Return project if current user is project owner."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    project_response = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project_id, permission="rwd"
    )
    project = verify_resource_response(project_response, "Project")
    return project


def can_read_flight(
    flight_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
    project: schemas.Project = Depends(can_read_project),
) -> models.Flight:
    """Return flight if current user is project owner, manager, or viewer."""
    flight_response = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight_id
    )
    flight = verify_resource_response(flight_response, "Flight")
    return flight


def can_read_write_flight(
    flight_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
    project: schemas.Project = Depends(can_read_write_project),
) -> models.Flight:
    """Return flight if current user is project owner or manager."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    flight_response = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight_id
    )
    flight = verify_resource_response(flight_response, "Flight")
    if flight and flight.read_only:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Flight currently locked. Please try again later.",
        )
    return flight


def can_read_write_delete_flight(
    flight_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
    project: schemas.Project = Depends(can_read_write_delete_project),
) -> models.Flight:
    """Return flight if current user is project owner."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    flight_response = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight_id
    )
    flight = verify_resource_response(flight_response, "Flight")
    return flight


def can_read_data_product(
    data_product_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
    flight: models.Flight = Depends(can_read_flight),
) -> models.DataProduct:
    """Return data product if it belongs to the flight and user has access."""
    data_product = crud.data_product.get(db, id=data_product_id)
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    if data_product.flight_id != flight.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data product does not belong to specified flight",
        )
    if not data_product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    return data_product


def can_read_or_public_data_product(
    project_id: UUID,
    flight_id: UUID,
    data_product_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> models.DataProduct:
    """Return data product if the current user can read it.

    Access is granted when the data product is publicly accessible (its file
    permission is_public is True, which is also set when the parent project is
    published) OR the user is a member of the project. Used by engagement
    endpoints so any authenticated user who can see a data product can engage
    with it, not only project members.
    """
    data_product = crud.data_product.get(db, id=data_product_id)
    if not data_product or not data_product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    # IDOR guards: the data product must belong to the flight, and the flight
    # to the project named in the path.
    flight = crud.flight.get(db, id=flight_id)
    if not flight or data_product.flight_id != flight.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data product does not belong to specified flight",
        )
    if flight.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Flight does not belong to specified project",
        )
    # Explicitly validate the parent hierarchy's soft-delete state rather than
    # relying solely on the deactivation cascade reaching the data product.
    project = crud.project.get(db, id=project_id)
    if not flight.is_active or not project or not project.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    # Publicly accessible files are readable by any authenticated user.
    file_permission = crud.file_permission.get_by_data_product(
        db, file_id=data_product_id
    )
    if file_permission and file_permission.is_public:
        return data_product
    # Otherwise require project membership.
    project_member = crud.project_member.get_by_project_and_member_id(
        db, project_uuid=project_id, member_id=current_user.id
    )
    if project_member:
        return data_product
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
    )


def can_read_write_data_product(
    data_product_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
    flight: models.Flight = Depends(can_read_write_flight),
) -> models.DataProduct:
    """Return data product if user has write access to the flight."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    data_product = crud.data_product.get(db, id=data_product_id)
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    if data_product.flight_id != flight.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data product does not belong to specified flight",
        )
    if not data_product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    return data_product


def can_read_write_delete_data_product(
    data_product_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
    flight: models.Flight = Depends(can_read_write_delete_flight),
) -> models.DataProduct:
    """Return data product if current user is project owner."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    data_product = crud.data_product.get(db, id=data_product_id)
    if not data_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data product not found"
        )
    if data_product.flight_id != flight.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data product does not belong to specified flight",
        )
    return data_product


def get_ip_settings(request: Request) -> Union[MetashapeQueryParams, ODMQueryParams]:
    """Get IP settings based on backend value from request query params.

    Args:
        request (Request): Request object containing query parameters.

    Raises:
        HTTPException: If backend value is invalid.

    Returns:
        Union[MetashapeQueryParams, ODMQueryParams]: IP settings.
    """
    params = dict(request.query_params)
    backend = params.get("backend")

    if backend == "odm":
        return ODMQueryParams(**params)
    elif backend == "metashape":
        return MetashapeQueryParams(**params)
    else:
        raise HTTPException(status_code=422, detail="Invalid backend value")
