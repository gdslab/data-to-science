"""Small string helpers with no application dependencies.

Kept free of imports from app.api, app.crud, and app.schemas so both the schema
layer and the API layer can use them without creating an import cycle.
"""


def truncate_to_bytes(value: str, max_bytes: int) -> str:
    """Truncates a string to fit a UTF-8 byte budget without splitting a character.

    File name limits are counted in bytes rather than characters, and a single
    character can encode to four bytes, so truncating by character count is not
    enough to stay inside them.

    Args:
        value (str): String to truncate.
        max_bytes (int): Maximum length of the encoded result.

    Returns:
        str: The string, shortened only if it did not already fit.
    """
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value

    # errors="ignore" drops the partial character left behind at the cut point
    return encoded[:max_bytes].decode("utf-8", errors="ignore")
