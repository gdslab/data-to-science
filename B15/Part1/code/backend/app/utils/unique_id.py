import base64
import random


def generate_unique_id() -> str:
    """
    Generates a random 64-bit integer and encodes it with base64url encoding (URL-safe).

    Returns:
        str: Unique ID.
    """
    # Generate a random 64-bit integer
    value = random.getrandbits(64)

    # Convert the integer to bytes
    byte_array = value.to_bytes(8, byteorder="little")

    # Encode bytes using base64url encoding (removes '+' and '/')
    base64_id = base64.urlsafe_b64encode(byte_array).decode("utf-8").rstrip("=")

    return base64_id
