import logging
from uuid import UUID

from fastapi import BackgroundTasks, Depends, HTTPException, status
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

logger = logging.getLogger("__name__")


reusable_oauth2 = security.OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{settings.API_V1_STR}/auth/access-token"
)


def get_db():
    """Create database session with lifespan of a single request."""
    db = SessionLocal()
    try:
        yield db
    except Exception as exception:
        logger.exception("Session raised exception - issuing rollback")
        logger.error(str(exception))
        db.rollback()
        exception_name = exception.__class__.__name__
        if exception_name == "JWTError" or exception_name == "JWSSignatureError":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Must sign in to access",
            )
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
        logger.error(str(e))
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
    background_tasks.add_task(fm.send_message, message)


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


def can_read_team(
    team_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> models.Team | None:
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
) -> models.Team | None:
    """Return team only if current user is owner of the team."""
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
) -> models.Project | None:
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
) -> models.Project | None:
    """Return project if current user is project owner or manager."""
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
) -> models.Project | None:
    """Return project if current user is project owner."""
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
) -> models.Flight | None:
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
) -> models.Flight | None:
    """Return flight if current user is project owner or manager."""
    flight = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight_id
    )
    if flight["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=flight["response_code"], detail=flight["message"]
        )
    return flight["result"]


def can_read_write_delete_flight(
    flight_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
    project: models.Project = Depends(can_read_write_project),
) -> models.Flight | None:
    """Return flight if current user is project owner."""
    flight = crud.flight.get_flight_by_id(
        db, project_id=project.id, flight_id=flight_id
    )
    if flight["response_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=flight["response_code"], detail=flight["message"]
        )
    return flight["result"]
