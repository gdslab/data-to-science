import uuid

from sqlalchemy.orm import Session

from app import crud
from app.schemas.refresh_token import RefreshTokenUpdate
from app.tests.utils.refresh_token import create_refresh_token_data
from app.tests.utils.user import create_user


def test_create_refresh_token(db: Session) -> None:
    """Test creating a new refresh token."""
    user = create_user(db)
    refresh_token_in = create_refresh_token_data(user.id)
    refresh_token = crud.refresh_token.create(db, obj_in=refresh_token_in)

    assert refresh_token
    assert refresh_token.jti
    assert refresh_token.user_id == user.id
    assert refresh_token.issued_at
    assert refresh_token.expires_at
    assert not refresh_token.revoked
    assert refresh_token.issued_at < refresh_token.expires_at


def test_get_refresh_token_by_jti(db: Session) -> None:
    """Test retrieving refresh token by JTI."""
    user = create_user(db)
    refresh_token_in = create_refresh_token_data(user.id)
    refresh_token = crud.refresh_token.create(db, obj_in=refresh_token_in)

    retrieved_token = crud.refresh_token.get_by_jti(db, jti=refresh_token.jti)

    assert retrieved_token
    assert retrieved_token.jti == refresh_token.jti
    assert retrieved_token.user_id == user.id


def test_get_refresh_token_by_jti_not_found(db: Session) -> None:
    """Test retrieving non-existent refresh token returns None."""
    random_jti = uuid.uuid4()
    retrieved_token = crud.refresh_token.get_by_jti(db, jti=random_jti)

    assert retrieved_token is None


def test_revoke_refresh_token(db: Session) -> None:
    """Test revoking a refresh token."""
    user = create_user(db)
    refresh_token_in = create_refresh_token_data(user.id)
    refresh_token = crud.refresh_token.create(db, obj_in=refresh_token_in)

    # Verify token is not revoked initially
    assert not refresh_token.revoked

    # Revoke the token
    revoked_token = crud.refresh_token.revoke(db, jti=refresh_token.jti)

    assert revoked_token
    assert revoked_token.revoked
    assert revoked_token.jti == refresh_token.jti


def test_revoke_nonexistent_refresh_token(db: Session) -> None:
    """Test revoking a non-existent refresh token returns None."""
    random_jti = uuid.uuid4()
    revoked_token = crud.refresh_token.revoke(db, jti=random_jti)

    assert revoked_token is None


def test_update_refresh_token(db: Session) -> None:
    """Test updating refresh token properties."""
    user = create_user(db)
    refresh_token_in = create_refresh_token_data(user.id)
    refresh_token = crud.refresh_token.create(db, obj_in=refresh_token_in)

    # Update the token to revoked status
    refresh_token_update = RefreshTokenUpdate(revoked=True)
    updated_token = crud.refresh_token.update(
        db, db_obj=refresh_token, obj_in=refresh_token_update
    )

    assert updated_token
    assert updated_token.revoked
    assert updated_token.jti == refresh_token.jti


def test_delete_refresh_token(db: Session) -> None:
    """Test deleting a refresh token."""
    user = create_user(db)
    refresh_token_in = create_refresh_token_data(user.id)
    refresh_token = crud.refresh_token.create(db, obj_in=refresh_token_in)

    deleted_token = crud.refresh_token.remove(db, id=refresh_token.jti)

    assert deleted_token
    assert deleted_token.jti == refresh_token.jti

    # Verify token is actually deleted
    retrieved_token = crud.refresh_token.get_by_jti(db, jti=refresh_token.jti)
    assert retrieved_token is None


def test_get_multi_refresh_tokens(db: Session) -> None:
    """Test retrieving multiple refresh tokens."""
    user1 = create_user(db)
    user2 = create_user(db)

    # Create tokens for both users
    token1 = crud.refresh_token.create(db, obj_in=create_refresh_token_data(user1.id))
    token2 = crud.refresh_token.create(db, obj_in=create_refresh_token_data(user2.id))

    tokens = crud.refresh_token.get_multi(db, skip=0, limit=10)

    assert len(tokens) >= 2
    token_jtis = [token.jti for token in tokens]
    assert token1.jti in token_jtis
    assert token2.jti in token_jtis
