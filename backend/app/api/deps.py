import logging
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal


logger = logging.getLogger("__name__")


reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/access-token"
)


def get_db():
    """Create database session with lifespan of a single request."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        logger.exception("Session raised exception - issuing rollback")
        db.rollback()
        raise
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    except Exception as e:
        logger.error(str(e))
    user = crud.user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def get_current_approved_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_approved(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account needs approval"
        )
    return current_user


def can_read_write_team(
    team_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> models.Team | None:
    """Return team only if current user is a member of the team."""
    team = crud.team.get_user_team(db, user_id=current_user.id, team_id=team_id)
    return team


def can_read_write_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> models.Project | None:
    """Return project only if current user is a member of the project."""
    project = crud.project.get_user_project(
        db, user_id=current_user.id, project_id=project_id
    )
    return project
