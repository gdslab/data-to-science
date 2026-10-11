import logging
import os
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_s3_configured() -> bool:
    """Check if S3 storage is configured for STAC publishing.

    Always returns False during tests to prevent accidental S3 uploads.
    """
    if os.environ.get("RUNNING_TESTS") == "1":
        return False
    return settings.AWS_S3_BUCKET_NAME is not None


def get_s3_client():
    """Create a boto3 S3 client.

    Uses explicit credentials from settings if configured, otherwise
    falls back to boto3's default credential chain (IAM roles, etc.).
    """
    kwargs = {}
    if settings.AWS_S3_REGION:
        kwargs["region_name"] = settings.AWS_S3_REGION
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    return boto3.client("s3", **kwargs)


def _get_s3_key_prefix() -> str:
    """Build the S3 key prefix from the API domain.

    Produces: d2s/{hostname}/
    E.g., https://ps2.d2s.org -> d2s/ps2.d2s.org
          http://localhost:8000 -> d2s/localhost
    """
    hostname = urlparse(settings.API_DOMAIN).hostname or "unknown"
    return f"d2s/{hostname}"


def build_s3_key(filepath: str, upload_dir: str) -> str:
    """Convert a local filepath to an S3 key by extracting the relative path.

    Prefixes with d2s/{hostname}/ to namespace within the bucket.
    E.g., d2s/ps2.d2s.org/projects/{project_id}/flights/.../file.tif
    """
    relative_path = str(Path(filepath).relative_to(upload_dir))
    return f"{_get_s3_key_prefix()}/{relative_path}"


def build_s3_url(s3_key: str) -> str:
    """Build the public S3 URL for an object."""
    region = settings.AWS_S3_REGION or "us-east-1"
    bucket = settings.AWS_S3_BUCKET_NAME
    return f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"


class S3UploadError(Exception):
    """Raised when an S3 upload fails. The message is safe to surface to users
    (no bucket names, file paths, or AWS error codes); the original exception
    is still logged server-side via logger.exception."""


def upload_file_to_s3(filepath: str, s3_key: str) -> str:
    """Upload a file to S3 and return the S3 URL.

    Uses boto3's upload_file which handles multipart uploads automatically
    for files larger than 8MB.

    Raises S3UploadError with a generic message on boto3 failure so the
    caller can handle rollback without leaking AWS details to users.
    """
    client = get_s3_client()
    try:
        client.upload_file(filepath, settings.AWS_S3_BUCKET_NAME, s3_key)
    except (ClientError, BotoCoreError):
        logger.exception(
            f"Failed to upload {filepath} to s3://{settings.AWS_S3_BUCKET_NAME}/{s3_key}"
        )
        raise S3UploadError(
            "Could not upload data to the configured S3 bucket. "
            "Please contact an administrator."
        )
    return build_s3_url(s3_key)


def delete_s3_objects(s3_keys: List[str]) -> bool:
    """Delete multiple objects from the S3 bucket.

    Returns True if every key in every batch was deleted successfully, False
    otherwise. Failures are logged; the function does not raise so callers can
    decide whether to preserve database state for retry.
    Handles batching (S3 delete_objects supports up to 1000 keys per call).
    """
    if not s3_keys:
        return True

    client = get_s3_client()
    bucket = settings.AWS_S3_BUCKET_NAME

    all_succeeded = True
    # Process in batches of 1000 (S3 API limit)
    for i in range(0, len(s3_keys), 1000):
        batch = s3_keys[i : i + 1000]
        try:
            response = client.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": key} for key in batch]},
            )
            errors = response.get("Errors", [])
            if errors:
                all_succeeded = False
                for error in errors:
                    logger.warning(
                        f"Failed to delete S3 object {error['Key']}: "
                        f"{error['Code']} - {error['Message']}"
                    )
        except (ClientError, BotoCoreError):
            all_succeeded = False
            logger.exception(f"Failed to delete S3 objects batch starting at index {i}")

    return all_succeeded


def parse_s3_key_from_url(s3_url: str) -> str:
    """Extract the S3 key from an S3 URL.

    Expects URL format: https://{bucket}.s3.{region}.amazonaws.com/{key}
    """
    # Remove the scheme and host portion to get the key
    # Format: https://{bucket}.s3.{region}.amazonaws.com/{key}
    parts = s3_url.split(".amazonaws.com/", 1)
    if len(parts) == 2:
        return parts[1]
    raise ValueError(f"Cannot parse S3 key from URL: {s3_url}")
