from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user_style import UserStyle
from app.schemas.user_style import UserStyleCreate, UserStyleUpdate


class CRUDUserStyle(CRUDBase[UserStyle, UserStyleCreate, UserStyleUpdate]):
    def create_with_data_product_and_user(
        self,
        db: Session,
        obj_in: UserStyleCreate,
        data_product_id: UUID,
        user_id: UUID,
    ) -> UserStyle:
        obj_in_data = jsonable_encoder(obj_in)
        user_style = self.model(
            **obj_in_data, data_product_id=data_product_id, user_id=user_id
        )
        with db as session:
            session.add(user_style)
            session.commit()
            session.refresh(user_style)
            return user_style

    def get_by_data_product_and_user(
        self, db: Session, data_product_id: UUID, user_id: UUID
    ) -> UserStyle | None:
        user_style_query = (
            select(UserStyle)
            .where(UserStyle.data_product_id == data_product_id)
            .where(UserStyle.user_id == user_id)
        )
        with db as session:
            user_style = session.scalar(user_style_query)
            return user_style


user_style = CRUDUserStyle(UserStyle)
