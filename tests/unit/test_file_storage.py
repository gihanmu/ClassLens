"""Tests for FileStorageBackend implementations (LocalFilesystemStorage and GoogleCloudStorageBackend)."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import shutil

from services.api.repository.file_storage import (
    LocalFilesystemStorage,
    GoogleCloudStorageBackend,
    get_file_storage,
    reset_file_storage,
)


def test_local_filesystem_storage_lifecycle():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        storage = LocalFilesystemStorage(base_dir=temp_dir)
        content = b"sample worksheet binary bytes"
        org_id = "test_org"
        assessment_id = "asm_123"
        filename = "worksheet_123.jpg"

        # Save file
        saved_name = storage.save_file(
            org_id=org_id,
            assessment_id=assessment_id,
            filename=filename,
            content=content,
            mime_type="image/jpeg",
        )
        assert saved_name == filename
        assert (temp_dir / org_id / assessment_id / filename).exists()

        # Check existence
        assert storage.file_exists(org_id, assessment_id, filename) is True
        assert storage.file_exists(org_id, assessment_id, "nonexistent.jpg") is False

        # Read back
        res = storage.get_file_bytes(org_id, assessment_id, filename)
        assert res is not None
        read_bytes, mime_type = res
        assert read_bytes == content
        assert mime_type == "image/jpeg"

        # Read nonexistent
        assert storage.get_file_bytes(org_id, assessment_id, "nonexistent.jpg") is None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_gcs_storage_backend_with_mocks():
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()

    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_blob.exists.return_value = True
    mock_blob.download_as_bytes.return_value = b"gcs image bytes"
    mock_blob.content_type = "image/jpeg"

    storage = GoogleCloudStorageBackend(bucket_name="test-bucket", client=mock_client)

    org_id = "org_a"
    assessment_id = "asm_456"
    filename = "submission_1.jpg"
    data = b"image content"

    saved_name = storage.save_file(org_id, assessment_id, filename, data, mime_type="image/jpeg")
    assert saved_name == filename
    mock_bucket.blob.assert_called_with("uploads/org_a/asm_456/submission_1.jpg")
    mock_blob.upload_from_string.assert_called_with(data, content_type="image/jpeg")

    assert storage.file_exists(org_id, assessment_id, filename) is True

    res = storage.get_file_bytes(org_id, assessment_id, filename)
    assert res is not None
    downloaded, mime = res
    assert downloaded == b"gcs image bytes"
    assert mime == "image/jpeg"


def test_get_file_storage_factory():
    reset_file_storage()
    # By default in test environment (PYTEST_CURRENT_TEST is set), it safely defaults to LocalFilesystemStorage
    storage = get_file_storage()
    assert isinstance(storage, LocalFilesystemStorage)
