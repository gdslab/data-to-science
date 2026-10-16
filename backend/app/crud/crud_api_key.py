from datetime import datetime, timezone
from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import Session, joinedload

from app.crud.base import CRUDBase
from app.models.api_key import APIKey
from app.models.enums.api_key_scope import APIKeyScope
from app.models.utils.utcnow import utcnow
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate, APIKeyUpdateRequest


class CRUDAPIKey(CRUDBase[APIKey, APIKeyCreate, APIKeyUpdate]):
    def create_with_user(
        self,
        db: Session,
        user_id: UUID,
        scopes: list[APIKeyScope],
        name: str | None = None,
    ) -> APIKey:
        # generate new api key (per-user limit is enforced by the endpoint)
        api_key_in = APIKeyCreate(
            api_key=token_urlsafe(), name=name, scopes=scopes, user_id=user_id
        )
        api_key = self.model(
            **api_key_in.model_dump(exclude={"scopes"}),
            scopes=[scope.value for scope in api_key_in.scopes],
        )
        with db as session:
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
        return api_key

    def get_multi_by_user(self, db: Session, user_id: UUID) -> list[APIKey]:
        # query for active api keys with matching user id, oldest first
        statement = (
            select(APIKey)
            .where(and_(APIKey.is_active, APIKey.user_id == user_id))
            .order_by(APIKey.created_at)
        )
        with db as session:
            return list(session.scalars(statement).all())

    def count_active_by_user(self, db: Session, user_id: UUID) -> int:
        # count active api keys with matching user id
        statement = (
            select(func.count())
            .select_from(APIKey)
            .where(and_(APIKey.is_active, APIKey.user_id == user_id))
        )
        with db as session:
            return session.scalar(statement) or 0

    def get_active_by_id_and_user(
        self, db: Session, api_key_id: UUID, user_id: UUID
    ) -> APIKey | None:
        # query for active api key with matching id that belongs to user
        statement = select(APIKey).where(
            and_(
                APIKey.is_active,
                APIKey.id == api_key_id,
                APIKey.user_id == user_id,
            )
        )
        with db as session:
            return session.scalar(statement)

    def get_by_api_key(self, db: Session, api_key: str) -> APIKey | None:
        # query for active api key with matching api_key
        statement = (
            select(APIKey)
            .options(joinedload(APIKey.owner))
            .where(and_(APIKey.is_active, APIKey.api_key == api_key))
        )
        with db as session:
            return session.scalar(statement)

    def record_use(self, db: Session, api_key_obj: APIKey) -> APIKey:
        # bump usage stats each time a request is authorized with the key
        api_key_in = APIKeyUpdate(
            last_used_at=datetime.now(timezone.utc),
            total_requests=api_key_obj.total_requests + 1,
        )
        return self.update(db, db_obj=api_key_obj, obj_in=api_key_in)

    def update_by_user(
        self,
        db: Session,
        api_key_id: UUID,
        user_id: UUID,
        obj_in: APIKeyUpdateRequest,
    ) -> APIKey | None:
        # only update keys that are active and belong to user
        api_key = self.get_active_by_id_and_user(
            db, api_key_id=api_key_id, user_id=user_id
        )
        if not api_key:
            return None
        update_data = obj_in.model_dump(exclude_unset=True)
        # scopes column stores plain strings
        if obj_in.scopes is not None:
            update_data["scopes"] = [scope.value for scope in obj_in.scopes]
        elif "scopes" in update_data:
            del update_data["scopes"]
        return self.update(db, db_obj=api_key, obj_in=update_data)

    def deactivate(self, db: Session, api_key_id: UUID, user_id: UUID) -> APIKey | None:
        # only deactivate keys that are active and belong to user
        active_api_key = self.get_active_by_id_and_user(
            db, api_key_id=api_key_id, user_id=user_id
        )
        if not active_api_key:
            return None
        statement = (
            update(APIKey)
            .where(APIKey.id == active_api_key.id)
            .values(is_active=False, deactivated_at=utcnow())
        )
        with db as session:
            session.execute(statement)
            session.commit()

        return self.get(db, id=active_api_key.id)


api_key = CRUDAPIKey(APIKey)
