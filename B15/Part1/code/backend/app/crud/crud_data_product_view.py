from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.data_product_view import DataProductView
from app.schemas.data_product_view import DataProductViewCreate, DataProductViewUpdate


class CRUDDataProductView(
    CRUDBase[DataProductView, DataProductViewCreate, DataProductViewUpdate]
):
    def create_if_not_recent(
        self,
        db: Session,
        *,
        data_product_id: UUID,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        window_hours: float = 0.5,  # Default deduplication window of 30 minutes
    ) -> Optional[DataProductView]:
        """Create a view record unless one already exists within the dedup window.

        Returns the new DataProductView on insert, or None if deduplicated.
        Raises ValueError if neither user_id nor session_id is provided.
        """
        if user_id is None and session_id is None:
            raise ValueError("Either user_id or session_id must be provided")

        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=window_hours)

        statement = select(DataProductView.id).where(
            DataProductView.data_product_id == data_product_id,
            DataProductView.viewed_at >= cutoff,
        )
        if user_id is not None:
            statement = statement.where(DataProductView.user_id == user_id)
        else:
            statement = statement.where(DataProductView.session_id == session_id)

        with db as session:
            existing = session.scalar(statement)
            if existing:
                return None

            view = DataProductView(
                data_product_id=data_product_id,
                user_id=user_id,
                session_id=session_id,
            )
            session.add(view)
            session.commit()
            session.refresh(view)
            return view

    def get_count_by_data_product_id(self, db: Session, data_product_id: UUID) -> int:
        """Return total view count for a data product."""
        statement = select(func.count(DataProductView.id)).where(
            DataProductView.data_product_id == data_product_id
        )
        with db as session:
            return session.scalar(statement) or 0


data_product_view = CRUDDataProductView(DataProductView)
