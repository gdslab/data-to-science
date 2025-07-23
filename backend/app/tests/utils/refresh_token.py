from datetime import datetime, timedelta, timezone
import uuid

from app.schemas.refresh_token import RefreshTokenCreate


def create_refresh_token_data(user_id: uuid.UUID) -> RefreshTokenCreate:
    """Helper to create RefreshTokenCreate with required datetime fields."""
    jti = uuid.uuid4()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=30)  # Default 30 days like in settings
    return RefreshTokenCreate(
        jti=jti, user_id=user_id, issued_at=now, expires_at=expire
    )
