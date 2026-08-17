from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, UUID4, field_validator

from app.utils.text_utils import truncate_to_bytes


class Storage(BaseModel):
    Path: str
    Type: str


# Matches the file name limit common to most filesystems, counted in bytes
# because the name arrives from a browser and can hold multi-byte characters.
MAX_ORIGINAL_FILENAME_BYTES = 255


class MetaData(BaseModel):
    # Stored verbatim as a data product's original_filename to preserve
    # provenance, so it is bounded and stripped of control characters here
    # rather than sanitized at rest. It never names a download, and the only
    # part of it that reaches a path is its extension, which is checked against
    # SUPPORTED_EXTENSIONS before use.
    filename: str
    filetype: str
    name: str
    relativePath: str
    type: str

    @field_validator("filename", mode="before")
    @classmethod
    def bound_filename(cls, value: Any) -> Any:
        """Strips control characters and caps the length.

        Deliberately truncates rather than rejects. This model validates the
        whole tusd hook payload, so raising here fails the hook itself: at
        pre-create the upload is refused with an opaque error, and at post-finish
        the bytes are already on the tus server while no data product record is
        ever created. Bounding what gets stored is the goal, not gatekeeping.

        Runs in "before" mode so the trimming happens ahead of the length cap
        instead of after it, where it could no longer bring an oversized name
        back under the limit.
        """
        if not isinstance(value, str):
            return value

        stripped = "".join(char for char in value if char.isprintable()).strip()

        return truncate_to_bytes(stripped, MAX_ORIGINAL_FILENAME_BYTES)


class Upload(BaseModel):
    ID: str
    Size: int
    SizeIsDeferred: bool
    Offset: int
    MetaData: MetaData
    IsPartial: bool
    IsFinal: bool
    PartialUploads: None
    Storage: Storage | None


class Header(BaseModel):
    Accept: List[str]
    Accept_Encoding: List[str] = Field(alias="Accept-Encoding")
    Accept_Language: List[str] = Field(alias="Accept-Language")
    Connection: List[str]
    Content_Length: Optional[List[str]] = Field(alias="Content-Length", default=None)
    Content_Type: Optional[List[str]] = Field(alias="Content-Type", default=None)
    Cookie: List[str]
    Dnt: Optional[List[str]] = None
    Host: List[str]
    Origin: List[str]
    Referer: Optional[List[str]] = None
    # Chrome Client Hints headers (added in newer browser versions)
    Sec_Ch_Ua: Optional[List[str]] = Field(alias="Sec-Ch-Ua", default=None)
    Sec_Ch_Ua_Mobile: Optional[List[str]] = Field(alias="Sec-Ch-Ua-Mobile", default=None)
    Sec_Ch_Ua_Platform: Optional[List[str]] = Field(alias="Sec-Ch-Ua-Platform", default=None)
    Sec_Fetch_Dest: Optional[List[str]] = Field(alias="Sec-Fetch-Dest", default=None)
    Sec_Fetch_Mode: Optional[List[str]] = Field(alias="Sec-Fetch-Mode", default=None)
    Sec_Fetch_Site: Optional[List[str]] = Field(alias="Sec-Fetch-Site", default=None)
    Tus_Resumable: List[str] = Field(alias="Tus-Resumable")
    Upload_Length: Optional[List[str]] = Field(alias="Upload-Length", default=None)
    Upload_Metadata: Optional[List[str]] = Field(alias="Upload-Metadata", default=None)
    Upload_Offset: Optional[List[str]] = Field(alias="Upload-Offset", default=None)
    User_Agent: List[str] = Field(alias="User-Agent")
    X_Forwarded_Host: List[str] = Field(alias="X-Forwarded-Host")
    X_Forwarded_Proto: List[str] = Field(alias="X-Forwarded-Proto")
    # custom headers
    X_Project_ID: Optional[List[UUID4]] = Field(alias="X-Project-Id", default=None)
    X_Flight_ID: Optional[List[UUID4]] = Field(alias="X-Flight-Id", default=None)
    X_Data_Type: Optional[List[str]] = Field(alias="X-Data-Type", default=None)
    X_Indoor_Project_ID: Optional[List[UUID4]] = Field(
        alias="X-Indoor-Project-Id", default=None
    )
    X_Treatment: Optional[List[str]] = Field(alias="X-Treatment", default=None)
    X_Annotation_ID: Optional[List[UUID4]] = Field(
        alias="X-Annotation-Id", default=None
    )
    X_Data_Product_ID: Optional[List[UUID4]] = Field(
        alias="X-Data-Product-Id", default=None
    )


class HTTPRequest(BaseModel):
    Method: str
    URI: str
    RemoteAddr: str
    Header: Header


class Event(BaseModel):
    Upload: Upload
    HTTPRequest: HTTPRequest


class TUSDHook(BaseModel):
    Type: str
    Event: Event
