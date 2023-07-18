import logging

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


def can_read_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> bool:
    """Team member with permission to read projects."""
    role = crud.team.get_user_team_role(db=db, team_id=team_id, user_id=current_user.id)
    if role:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User cannot view team"
        )


def can_read_write_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> bool:
    """Team member with permission to create, read, edit, and remove projects."""
    role = crud.team.get_user_team_role(db=db, team_id=team_id, user_id=current_user.id)
    if role == "Manager":
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User cannot update team",
        )


def can_read_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> bool:
    """Project member with permission to read a project's datasets."""
    role = crud.project.get_user_project_role(
        db=db, project_id=project_id, user_id=current_user.id
    )
    if role:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User cannot view project"
        )


def can_read_write_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_approved_user),
) -> bool:
    """Project member with permission to create, read, edit, and remove datasets."""
    role = crud.project.get_user_project_role(
        db=db, project_id=project_id, user_id=current_user.id
    )
    if role == "Manager":
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User cannot update project",
        )
