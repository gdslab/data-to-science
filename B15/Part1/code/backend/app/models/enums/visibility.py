from enum import Enum

from sqlalchemy import Enum as SAEnum


class Visibility(str, Enum):
    OWNER = "OWNER"
    PROJECT = "PROJECT"


# Reuse this in any model column that needs to be a visibility enum
VisibilityEnum = SAEnum(
    Visibility, name="visibility_scope", native_enum=True, create_type=False
)
