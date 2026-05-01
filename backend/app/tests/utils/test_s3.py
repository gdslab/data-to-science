import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from app.core.config import settings
from app.utils import s3 as s3_utils


def test_is_s3_configured_returns_false_during_tests(monkeypatch):
    """The conftest sets RUNNING_TESTS=1, so is_s3_configured must always be False."""
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "some-bucket")
    assert os.environ.get("RUNNING_TESTS") == "1"
    assert s3_utils.is_s3_configured() is False


def test_is_s3_configured_true_when_bucket_set_and_not_testing(monkeypatch):
    monkeypatch.delenv("RUNNING_TESTS", raising=False)
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "some-bucket")
    assert s3_utils.is_s3_configured() is True


def test_is_s3_configured_false_when_bucket_unset(monkeypatch):
    monkeypatch.delenv("RUNNING_TESTS", raising=False)
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", None)
    assert s3_utils.is_s3_configured() is False


def test_build_s3_key_uses_hostname_prefix(monkeypatch):
    monkeypatch.setattr(settings, "API_DOMAIN", "https://ps2.d2s.org")
    upload_dir = "/static"
    filepath = "/static/projects/abc/flights/def/data_products/ghi/file.tif"

    key = s3_utils.build_s3_key(filepath, upload_dir)

    assert key == "d2s/ps2.d2s.org/projects/abc/flights/def/data_products/ghi/file.tif"


def test_build_s3_key_localhost_hostname(monkeypatch):
    monkeypatch.setattr(settings, "API_DOMAIN", "http://localhost:8000")
    key = s3_utils.build_s3_key("/static/foo/bar.tif", "/static")
    assert key == "d2s/localhost/foo/bar.tif"


def test_build_s3_key_falls_back_to_unknown_when_no_hostname(monkeypatch):
    monkeypatch.setattr(settings, "API_DOMAIN", "")
    key = s3_utils.build_s3_key("/static/x.tif", "/static")
    assert key.startswith("d2s/unknown/")


def test_build_s3_url_uses_region_and_bucket(monkeypatch):
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "my-bucket")
    monkeypatch.setattr(settings, "AWS_S3_REGION", "us-west-2")

    url = s3_utils.build_s3_url("d2s/host/path/file.tif")

    assert url == "https://my-bucket.s3.us-west-2.amazonaws.com/d2s/host/path/file.tif"


def test_build_s3_url_defaults_region_to_us_east_1(monkeypatch):
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "my-bucket")
    monkeypatch.setattr(settings, "AWS_S3_REGION", None)
    url = s3_utils.build_s3_url("k")
    assert "s3.us-east-1.amazonaws.com" in url


def test_parse_s3_key_round_trips_with_build_s3_url(monkeypatch):
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "my-bucket")
    monkeypatch.setattr(settings, "AWS_S3_REGION", "us-east-1")
    key = "d2s/host.example.com/projects/p/file.tif"

    url = s3_utils.build_s3_url(key)

    assert s3_utils.parse_s3_key_from_url(url) == key


def test_parse_s3_key_raises_on_malformed_url():
    with pytest.raises(ValueError):
        s3_utils.parse_s3_key_from_url("https://example.com/not-an-s3-url")


def test_upload_file_to_s3_uploads_and_returns_url(monkeypatch):
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "my-bucket")
    monkeypatch.setattr(settings, "AWS_S3_REGION", "us-east-1")
    fake_client = MagicMock()
    monkeypatch.setattr(s3_utils, "get_s3_client", lambda: fake_client)

    with tempfile.NamedTemporaryFile(suffix=".tif") as tmp:
        url = s3_utils.upload_file_to_s3(tmp.name, "d2s/host/file.tif")

        fake_client.upload_file.assert_called_once_with(
            tmp.name, "my-bucket", "d2s/host/file.tif"
        )
        assert url == "https://my-bucket.s3.us-east-1.amazonaws.com/d2s/host/file.tif"


def test_upload_file_to_s3_raises_sanitized_error_on_client_error(monkeypatch):
    """Boto ClientError (e.g. NoSuchBucket) must be re-raised as a generic
    S3UploadError so the bucket name / key / AWS error code don't leak to the
    user-facing job error response."""
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "secret-bucket")
    fake_client = MagicMock()
    fake_client.upload_file.side_effect = ClientError(
        {"Error": {"Code": "NoSuchBucket", "Message": "bucket does not exist"}},
        "CreateMultipartUpload",
    )
    monkeypatch.setattr(s3_utils, "get_s3_client", lambda: fake_client)

    with pytest.raises(s3_utils.S3UploadError) as exc_info:
        s3_utils.upload_file_to_s3("/static/some/file.tif", "d2s/host/file.tif")

    msg = str(exc_info.value)
    assert "secret-bucket" not in msg
    assert "/static/some/file.tif" not in msg
    assert "NoSuchBucket" not in msg


def test_upload_file_to_s3_raises_sanitized_error_on_botocore_error(monkeypatch):
    """Connection-level BotoCoreError must also be sanitized."""
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "secret-bucket")
    fake_client = MagicMock()
    fake_client.upload_file.side_effect = EndpointConnectionError(
        endpoint_url="https://s3.example.com"
    )
    monkeypatch.setattr(s3_utils, "get_s3_client", lambda: fake_client)

    with pytest.raises(s3_utils.S3UploadError) as exc_info:
        s3_utils.upload_file_to_s3("/static/some/file.tif", "d2s/host/file.tif")

    msg = str(exc_info.value)
    assert "secret-bucket" not in msg
    assert "s3.example.com" not in msg


def test_delete_s3_objects_noop_on_empty(monkeypatch):
    """Empty input must short-circuit BEFORE creating the S3 client to avoid
    unnecessary credential resolution / network access."""
    fake_get_client = MagicMock()
    monkeypatch.setattr(s3_utils, "get_s3_client", fake_get_client)

    assert s3_utils.delete_s3_objects([]) is True

    fake_get_client.assert_not_called()


def test_delete_s3_objects_returns_true_on_full_success(monkeypatch):
    """When every batch comes back with no errors, the helper reports success."""
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "my-bucket")
    fake_client = MagicMock()
    fake_client.delete_objects.return_value = {"Errors": []}
    monkeypatch.setattr(s3_utils, "get_s3_client", lambda: fake_client)

    keys = [f"k{i}" for i in range(2500)]
    assert s3_utils.delete_s3_objects(keys) is True

    # Expect 3 batches: 1000, 1000, 500
    assert fake_client.delete_objects.call_count == 3
    batch_sizes = [
        len(call.kwargs["Delete"]["Objects"])
        for call in fake_client.delete_objects.call_args_list
    ]
    assert batch_sizes == [1000, 1000, 500]


def test_delete_s3_objects_returns_false_on_client_error(monkeypatch, caplog):
    """ClientError (e.g. auth failure) must be logged and reported as failure
    so callers can preserve the s3_url columns for retry."""
    fake_client = MagicMock()
    fake_client.delete_objects.side_effect = ClientError(
        {"Error": {"Code": "Boom", "Message": "nope"}}, "DeleteObjects"
    )
    monkeypatch.setattr(s3_utils, "get_s3_client", lambda: fake_client)

    assert s3_utils.delete_s3_objects(["k1", "k2"]) is False


def test_delete_s3_objects_returns_false_on_botocore_error(monkeypatch, caplog):
    """Connection-level BotoCoreError (no endpoint, network down, etc.) must
    not propagate, but must be reported as failure to preserve s3_url columns."""
    fake_client = MagicMock()
    fake_client.delete_objects.side_effect = EndpointConnectionError(
        endpoint_url="https://s3.example.com"
    )
    monkeypatch.setattr(s3_utils, "get_s3_client", lambda: fake_client)

    assert s3_utils.delete_s3_objects(["k1", "k2"]) is False


def test_delete_s3_objects_returns_false_on_per_key_errors(monkeypatch, caplog):
    """Per-key errors in the response must be logged and downgrade the overall
    return value to False."""
    fake_client = MagicMock()
    fake_client.delete_objects.return_value = {
        "Errors": [{"Key": "k1", "Code": "AccessDenied", "Message": "no perms"}]
    }
    monkeypatch.setattr(s3_utils, "get_s3_client", lambda: fake_client)

    with caplog.at_level("WARNING", logger="app.utils.s3"):
        assert s3_utils.delete_s3_objects(["k1", "k2"]) is False

    assert any("k1" in rec.message and "AccessDenied" in rec.message for rec in caplog.records)
