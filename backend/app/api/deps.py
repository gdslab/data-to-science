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
    subject: str, recipient: EmailStr, body: str, background_tasks: BackgroundTasks
):
    message = MessageSchema(
        subject=subject, recipients=[recipient], body=body, subtype=MessageType.html
    )
    background_tasks.add_task(fm.send_message, message)


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    token_data = decode_jwt(token)
    if token_data.sub:
        user = crud.user.get(db, id=token_data.sub)
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
    team = crud.team.get_user_team(db, user_id=current_user.id, team_id=team_id)
    return team


def can_read_write_team(
    team_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> models.Team | None:
    """Return team only if current user is owner of the team."""
    team = crud.team.get_user_team(
        db, user_id=current_user.id, team_id=team_id, only_owner=True
    )
    return team


def can_read_write_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> models.Project | None:
    """Return project if current user is project member or team member."""
    project = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project_id
    )
    return project


def can_read_write_flight(
    flight_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
    project: models.Project = Depends(can_read_write_project),
) -> models.Flight | None:
    """Return flight only if current user is a member of the project."""
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    flight = crud.flight.get(db, id=flight_id)
    return flight
