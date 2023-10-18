import glob
import os
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.single_use_token import SingleUseToken
from app.models.user import User
from app.schemas.single_use_token import SingleUseTokenCreate
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_id(self, db: Session, *, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        with db as session:
            user = session.scalar(stmt)
            if user:
                set_url_attr(user)
            return user

    def get_by_email(self, db: Session, *, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        with db as session:
            user = session.scalar(stmt)
            if user:
                set_url_attr(user)
            return user

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        user = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
        )
        with db as session:
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

    def create_single_use_token(
        self, db: Session, obj_in: SingleUseTokenCreate, user_id: UUID
    ) -> SingleUseToken:
        db_obj = SingleUseToken(**obj_in.model_dump(), user_id=user_id)
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        return db_obj

    def get_single_use_token(
        self, db: Session, token_hash: str
    ) -> SingleUseToken | None:
        stmt = select(SingleUseToken).where(SingleUseToken.token == token_hash)
        with db as session:
            token = session.scalar(stmt)
            return token

    def remove_single_use_token(
        self, db: Session, db_obj: SingleUseToken
    ) -> SingleUseToken:
        with db as session:
            session.delete(db_obj)
            session.commit()
            return db_obj

    def get_multi_by_query(
        self,
        db: Session,
        q: str | None = "",
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        statement = (
            select(User).where(User.is_approved).where(User.full_name.contains(q))
        )
        with db as session:
            users = session.scalars(statement).all()
        return users

    def update(
        self, db: Session, *, db_obj: User, obj_in: UserUpdate | dict[str, Any]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> User | None:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_approved(self, user: User) -> bool:
        return user.is_approved

    def is_email_confirmed(self, user: User) -> bool:
        return user.is_email_confirmed

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser


def find_profile_img(user_id: str) -> str | None:
    user_static_dir = os.path.join(settings.UPLOAD_DIR, "users", user_id)
    profile_img = glob.glob(os.path.join(user_static_dir, "*.png")) + glob.glob(
        os.path.join(user_static_dir, "*.jpg")
    )
    if len(profile_img) > 0:
        return os.path.basename(profile_img[0])
    else:
        return None


def set_url_attr(user: User):
    profile_img = find_profile_img(str(user.id))
    if profile_img:
        profile_url = f"{settings.STATIC_URL}/users/{str(user.id)}/{profile_img}"
        setattr(user, "profile_url", profile_url)


user = CRUDUser(User)
