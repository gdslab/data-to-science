from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, UUID4


class STACError(BaseModel):
    code: str
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class ItemStatus(BaseModel):
    item_id: str
    is_published: bool
    item_url: Optional[str] = None
    error: Optional[STACError] = None


class STACReport(BaseModel):
    collection_id: UUID4
    items: List[ItemStatus]
    is_published: bool
    collection_url: Optional[str] = None
    error: Optional[STACError] = None


class STACPreview(BaseModel):
    collection_id: UUID4
    collection: Dict[str, Any]
    items: List[Dict[str, Any]]
    is_published: bool
    collection_url: Optional[str] = None
    failed_items: Optional[List[ItemStatus]] = None


class STACMetadataRequest(BaseModel):
    """Request body for STAC operations (preview generation and catalog publishing)."""

    sci_doi: Optional[str] = None
    sci_citation: Optional[str] = None
    license: Optional[str] = None
    custom_titles: Optional[Dict[str, str]] = None


STACResponse = Union[STACReport, STACPreview]
