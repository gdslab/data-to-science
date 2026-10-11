from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import check_token_expired, sign_map_tile_payload
from app.models.single_use_token import SingleUseToken
from app.tests.utils.utils import expected_tile_signature


def test_check_token_expired_returns_true_for_old_token() -> None:
    """Token created 90 minutes ago should be expired with a 60-minute limit."""
    token = SingleUseToken()
    token.created_at = datetime.now(timezone.utc) - timedelta(minutes=90)
    assert check_token_expired(token, minutes=60) is True


def test_check_token_expired_returns_false_for_fresh_token() -> None:
    """Token created 5 minutes ago should not be expired with a 60-minute limit."""
    token = SingleUseToken()
    token.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    assert check_token_expired(token, minutes=60) is False


def test_sign_map_tile_payload_matches_varnish_hmac(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Signature is the hex HMAC of the expiry prepended to the payload."""
    monkeypatch.setattr("app.core.security.time.time", lambda: 1_700_000_000)

    signature, expires = sign_map_tile_payload("some-payload")

    assert expires == 1_700_000_000 + 600
    assert signature == expected_tile_signature(expires, "some-payload")


def test_sign_map_tile_payload_accepts_custom_expiration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Expiration argument offsets the returned timestamp."""
    monkeypatch.setattr("app.core.security.time.time", lambda: 1_700_000_000)

    _, expires = sign_map_tile_payload("some-payload", expiration=30)

    assert expires == 1_700_000_000 + 30
