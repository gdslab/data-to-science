from enum import Enum


# read covers GET/HEAD/OPTIONS, create covers POST, update covers PUT/PATCH,
# and delete covers DELETE requests
class APIKeyScope(str, Enum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


ALL_API_KEY_SCOPES: list[APIKeyScope] = [
    APIKeyScope.READ,
    APIKeyScope.CREATE,
    APIKeyScope.UPDATE,
    APIKeyScope.DELETE,
]

# maximum number of active api keys a user may hold at once
MAX_ACTIVE_API_KEYS = 5
