import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize("field_name", ["SECRET_KEY", "TILE_SIGNING_SECRET_KEY"])
def test_validate_secret_keys_rejects_changeme_placeholder(field_name: str) -> None:
    """A secret still set to a CHANGEME placeholder is rejected at startup."""
    placeholder = "CHANGEME-placeholder-value-at-least-32-chars"

    with pytest.raises(ValidationError, match="placeholder"):
        Settings(**{field_name: placeholder})
