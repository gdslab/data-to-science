from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.refresh_token import RefreshToken
from app.schemas.refresh_token import RefreshTokenCreate, RefreshTokenUpdate


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
            token_update = RefreshTokenUpdate(revoked=True)
            return self.update(db, db_obj=token, obj_in=token_update)
        return None


refresh_token = CRUDRefreshToken(RefreshToken)
