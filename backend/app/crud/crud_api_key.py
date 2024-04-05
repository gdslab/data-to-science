from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.api_key import APIKey
from app.models.utils.user import utcnow
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate


class CRUDAPIKey(CRUDBase[APIKey, APIKeyCreate, APIKeyUpdate]):
    def create_with_user(self, db: Session, user_id: UUID) -> APIKey:
        # check if user already has key
        existing_api_key = self.get_by_user(db, user_id=user_id)
        if existing_api_key:
            # deactivate existing key
            deactivated_api_key = self.deactivate(db, user_id=user_id)
            if deactivated_api_key.is_active:
                raise Exception
        # generate new api key
        api_key_in = APIKeyCreate(api_key=token_urlsafe(), user_id=user_id)
        api_key = self.model(**api_key_in.model_dump())
        with db as session:
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
        return api_key

    def get_by_user(self, db: Session, user_id: UUID) -> APIKey | None:
        # query for active api key with matching user id
        statement = select(APIKey).where(
            and_(APIKey.is_active, APIKey.user_id == user_id)
        )
        with db as session:
            file_permission = session.scalar(statement)
            return file_permission

    def deactivate(self, db: Session, user_id: UUID) -> APIKey | None:
        # query to update existing api key is_active property
        active_api_key = self.get_by_user(db, user_id=user_id)
        if active_api_key:
            statement = (
                update(APIKey)
                .where(APIKey.id == active_api_key.id)
                .values(is_active=False, deactivated_at=utcnow())
            )
            with db as session:
                session.execute(statement)
                session.commit()

            return crud.api_key.get(db, id=active_api_key.id)
        else:
            return None


api_key = CRUDAPIKey(APIKey)
