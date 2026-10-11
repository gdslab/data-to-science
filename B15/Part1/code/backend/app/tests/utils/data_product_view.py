from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session

from app import crud
from app.models.data_product_view import DataProductView
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.user import create_user


def create_data_product_view(
    db: Session,
    data_product_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    session_id: Optional[str] = None,
    viewed_at: Optional[datetime] = None,
) -> DataProductView:
    """Create a DataProductView row for testing.

    Provide viewed_at to backdate the row (e.g., to test the dedup window).
    Either user_id or session_id must be set; if neither is given, a new user
    is created and its id is used.
    """
    if data_product_id is None:
        sample = SampleDataProduct(db)
        data_product_id = sample.obj.id
    if user_id is None and session_id is None:
        user_id = create_user(db).id

    view = crud.data_product_view.create_if_not_recent(
        db,
        data_product_id=data_product_id,
        user_id=user_id,
        session_id=session_id,
        window_hours=0,
    )
    assert view is not None, "create_data_product_view: row was unexpectedly deduped"

    if viewed_at is not None:
        stmt = (
            update(DataProductView)
            .where(DataProductView.id == view.id)
            .values(viewed_at=viewed_at)
        )
        with db as session:
            session.execute(stmt)
            session.commit()
        with db as session:
            view = session.get(DataProductView, view.id)

    return view
