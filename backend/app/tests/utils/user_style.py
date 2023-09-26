from uuid import UUID

from sqlalchemy.orm import Session

from app import crud
from app.models.user_style import UserStyle
from app.schemas.user_style import UserStyleCreate
from app.tests.utils.DefaultUserStyle import DefaultUserStyle


def create_user_style(db: Session, data_product_id: UUID, user_id: UUID) -> UserStyle:
    default_user_styles = DefaultUserStyle()
    return crud.user_style.create_with_data_product_and_user(
        db,
        obj_in=UserStyleCreate(settings=default_user_styles.__dict__),
        data_product_id=data_product_id,
        user_id=user_id,
    )
