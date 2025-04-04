import logging
from typing import Optional, Union
from uuid import UUID

from fastapi import BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from fastapi_mail import MessageSchema, MessageType
from jose import jwt
from jose.exceptions import JWTError
from pydantic import EmailStr, ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.core.mail import fm
from app.db.session import SessionLocal
from app.api.utils import is_valid_api_key
from app.schemas.raw_data import MetashapeQueryParams, ODMQueryParams

logger = logging.getLogger("__name__")


header_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)
reusable_oauth2 = security.OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{settings.API_V1_STR}/auth/access-token"
)
# used for endpoints that can be authorized with api key or jwt token
reusable_oauth2_optional = security.OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{settings.API_V1_STR}/auth/access-token", auto_error=False
)


def get_db():
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
        else:
            if exception_name != "HTTPException":
                logger.exception("Uncaught error")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unexpected error has occurred",
                )
            else:
                raise exception
    finally:
        db.close()


def decode_jwt(token: str) -> schemas.TokenPayload:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden",
        )
    except Exception as e:
        logger.exception("Failed to decode jwt")
    return token_data


def send_email(
    subject: str,
    recipients: list[EmailStr],
    body: str,
    background_tasks: BackgroundTasks,
):
    message = MessageSchema(
        subject=subject, recipients=recipients, body=body, subtype=MessageType.html
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
    token_data = decode_jwt(token)
    if token_data.sub:
        user = crud.user.get_by_id(db, user_id=token_data.sub)
    else:
        user = None
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
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
        token_data = decode_jwt(token)
        if token_data.sub:
            user = crud.user.get_by_id(db, user_id=token_data.sub)

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
        token_data = decode_jwt(token)
        if token_data.sub:
            user = crud.user.get_by_id(db, user_id=token_data.sub)

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
        db, user_id=current_user.id, team_id=team_id, permission="readwrite"
    )
    if not team:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    return team


def can_read_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> Optional[schemas.Project]:
    """Return project is current user is project owner, manager, or viewer."""
    project = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project_id, permission="r"
    )
    if project["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=project["response_code"], detail=project["message"]
        )
    return project["result"]


def can_read_write_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> Optional[models.Project]:
    """Return project if current user is project owner or manager."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    project = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project_id, permission="rw"
    )
    if project["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=project["response_code"], detail=project["message"]
        )
    return project["result"]


def can_read_write_project_with_jwt_or_api_key(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user_by_jwt_or_api_key),
) -> Optional[models.Project]:
    """Return project if current user is project owner or manager."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    project = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project_id, permission="rw"
    )
    if project["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=project["response_code"], detail=project["message"]
        )
    return project["result"]


def can_read_write_delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> Optional[models.Project]:
    """Return project if current user is project owner."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    project = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project_id, permission="rwd"
    )
    if project["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=project["response_code"], detail=project["message"]
        )
    return project["result"]


def can_read_flight(
    flight_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
    project: models.Project = Depends(can_read_project),
) -> Optional[models.Flight]:
    """Return flight if current user is project owner, manager, or viewer."""
    flight = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight_id
    )
    if flight["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=flight["response_code"], detail=flight["message"]
        )
    return flight["result"]


def can_read_write_flight(
    flight_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
    project: models.Project = Depends(can_read_write_project),
) -> Optional[models.Flight]:
    """Return flight if current user is project owner or manager."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    flight = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight_id
    )
    if flight["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=flight["response_code"], detail=flight["message"]
        )
    if flight["result"] and flight["result"].read_only:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Flight currently locked. Please try again later.",
        )
    return flight["result"]


def can_read_write_delete_flight(
    flight_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
    project: models.Project = Depends(can_read_write_delete_project),
) -> Optional[models.Flight]:
    """Return flight if current user is project owner."""
    if current_user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )
    flight = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight_id
    )
    if flight["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=flight["response_code"], detail=flight["message"]
        )
    return flight["result"]


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
