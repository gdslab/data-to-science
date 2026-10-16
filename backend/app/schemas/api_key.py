from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums.api_key_scope import APIKeyScope


# base properties
class APIKeyBase(BaseModel):
    user_id: UUID | None = None


class APIKeyCreate(APIKeyBase):
    api_key: str
    name: str | None = None
    scopes: list[APIKeyScope]
    user_id: UUID


class APIKeyUpdate(APIKeyBase):
    deactivated_at: datetime | None = None
    is_active: bool | None = None
    last_used_at: datetime | None = None
    name: str | None = None
    scopes: list[APIKeyScope] | None = None
    total_requests: int | None = None


class APIKeyInDBBase(APIKeyBase):
    id: UUID
    api_key: str
    created_at: datetime
    is_active: bool
    last_used_at: datetime | None = None
    name: str | None = None
    scopes: list[APIKeyScope]
    total_requests: int
    user_id: UUID
    deactivated_at: datetime | None = None


class APIKey(APIKeyInDBBase):
    pass


# properties to receive via API when requesting a new key
class APIKeyRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    scopes: List[APIKeyScope] = Field(min_length=1)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: Optional[str]) -> Optional[str]:
        """Strip whitespace and convert empty strings to None."""
        if value is None:
            return None
        stripped = value.strip()
        return stripped if stripped else None

    @field_validator("scopes")
    @classmethod
    def dedupe_scopes(cls, value: List[APIKeyScope]) -> List[APIKeyScope]:
        """Remove duplicate scopes while preserving order."""
        return list(dict.fromkeys(value))


# properties to receive via API when updating an existing key
class APIKeyUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    scopes: Optional[List[APIKeyScope]] = Field(None, min_length=1)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: Optional[str]) -> Optional[str]:
        """Strip whitespace and convert empty strings to None."""
        if value is None:
            return None
        stripped = value.strip()
        return stripped if stripped else None

    @field_validator("scopes")
    @classmethod
    def dedupe_scopes(
        cls, value: Optional[List[APIKeyScope]]
    ) -> Optional[List[APIKeyScope]]:
        """Remove duplicate scopes while preserving order."""
        if value is None:
            return None
        return list(dict.fromkeys(value))
