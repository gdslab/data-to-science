from app.utils.text_utils import truncate_to_bytes


def test_truncate_to_bytes_leaves_a_short_string_alone() -> None:
    """A string already inside the budget comes back unchanged."""
    assert truncate_to_bytes("Corn Trial", 48) == "Corn Trial"


def test_truncate_to_bytes_counts_bytes_not_characters() -> None:
    """A multi-byte string is measured by its encoded length.

    U+20000 encodes to four bytes in UTF-8, so a 48 byte budget holds 12 of them
    where a character based cap would have kept 48.
    """
    truncated = truncate_to_bytes("\U00020000" * 100, 48)

    assert len(truncated.encode("utf-8")) == 48
    assert len(truncated) == 12


def test_truncate_to_bytes_does_not_split_a_character() -> None:
    """Cutting mid-character drops the partial rather than emitting a broken byte.

    A four byte character against a budget that only fits three of its bytes has
    to be dropped whole, leaving the result under budget.
    """
    truncated = truncate_to_bytes("\U00020000" * 10, 6)

    assert truncated == "\U00020000"
    assert len(truncated.encode("utf-8")) == 4
    # still valid UTF-8, which a naive byte slice would not be
    truncated.encode("utf-8").decode("utf-8")


def test_truncate_to_bytes_handles_an_empty_string() -> None:
    """An empty string is returned as-is rather than erroring."""
    assert truncate_to_bytes("", 48) == ""
