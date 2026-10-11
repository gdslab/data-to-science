from datetime import datetime, timedelta, timezone
from typing import Any, cast
from uuid import UUID

from sqlalchemy import CursorResult, delete, or_, select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.refresh_token import RefreshToken
from app.schemas.refresh_token import RefreshTokenCreate, RefreshTokenUpdate

# Only purge revoked rows once they are well past the reuse grace window, so a
# just-rotated token is never deleted while its grace window is still live.
REVOKED_RETENTION = timedelta(days=1)


class CRUDRefreshToken(CRUDBase[RefreshToken, RefreshTokenCreate, RefreshTokenUpdate]):
    def get_by_jti(self, db: Session, *, jti: UUID) -> RefreshToken | None:
        """Get refresh token by JTI (JWT ID)."""
        statement = select(RefreshToken).where(RefreshToken.jti == jti)
        with db as session:
            return session.scalar(statement)

    def revoke(self, db: Session, *, jti: UUID) -> RefreshToken | None:
        """Revoke a refresh token by JTI."""
        token = self.get_by_jti(db, jti=jti)
        if token:
            token_update = RefreshTokenUpdate(
                revoked=True, revoked_at=datetime.now(timezone.utc)
            )
            return self.update(db, db_obj=token, obj_in=token_update)
        return None

    def delete_stale(self, db: Session) -> int:
        """Purge stale refresh tokens and return the number of rows deleted.

        Removes tokens that are past their expiry, plus tokens revoked longer ago
        than REVOKED_RETENTION (safely beyond the reuse grace window). Returns the
        deleted row count.
        """
        now = datetime.now(timezone.utc)
        statement = delete(RefreshToken).where(
            or_(
                RefreshToken.expires_at < now,
                RefreshToken.revoked.is_(True)
                & (RefreshToken.revoked_at < now - REVOKED_RETENTION),
            )
        )
        with db as session:
            result = cast("CursorResult[Any]", session.execute(statement))
            session.commit()
        return result.rowcount


refresh_token = CRUDRefreshToken(RefreshToken)
