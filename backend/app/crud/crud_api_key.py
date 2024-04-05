from datetime import datetime
from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.orm import joinedload, Session

from app import crud
from app.api.deps import can_read_project
from app.crud.base import CRUDBase
from app.db.session import SessionLocal
from app.models.api_key import APIKey
from app.models.data_product import DataProduct
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
            api_key = session.scalar(statement)
            return api_key

    def get_by_api_key(self, db: Session, api_key: str) -> APIKey | None:
        # query for active api key with matching api_key
        statement = (
            select(APIKey)
            .options(joinedload(APIKey.owner))
            .where(and_(APIKey.is_active, APIKey.api_key == api_key))
        )
        with db as session:
            api_key = session.scalar(statement)
            return api_key

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


def api_key_can_access_static_file(data_product: DataProduct, api_key: str):
    """Verify if user associated with API key is authorized to access the
    requested data product.

    Args:
        data_product (DataProduct): Data product that was requested.
        api_key (str): API key included in request.

    Returns:
        _type_: True if authorized to access, False otherwise.
    """
    # create database session
    db = SessionLocal()
    # get api key db obj
    api_key_obj = crud.api_key.get_by_api_key(db, api_key)
    if api_key_obj:
        # user associated with api key
        user = api_key_obj.owner
        # flight associated with data product
        flight = crud.flight.get(db, id=data_product.flight_id)
        # check if can read flight
        if can_read_project(db=db, project_id=flight.project_id, current_user=user):
            # update last accessed date and total requests
            api_key_in = APIKeyUpdate(
                last_used_at=datetime.utcnow(),
                total_requests=api_key_obj.total_requests + 1,
            )
            crud.api_key.update(db, db_obj=api_key_obj, obj_in=api_key_in)
            return True

    return False


api_key = CRUDAPIKey(APIKey)
