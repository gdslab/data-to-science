from fastapi import HTTPException, status


class PermissionDenied(HTTPException):
    """Exception raised when a user lacks required permissions."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ResourceNotFound(HTTPException):
    """Exception raised when a requested resource cannot be found."""

    def __init__(self, resource: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found"
        )
