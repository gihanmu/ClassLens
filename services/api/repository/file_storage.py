"""Storage abstraction for student worksheet image files.

Provides seamless support for:
- LocalFilesystemStorage (local development & isolated automated tests)
- GoogleCloudStorageBackend (production Cloud Run deployment with GCS bucket)
"""

from __future__ import annotations

import logging
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

from services.api.config import settings
from services.api.repository.storage_config import get_uploads_dir

logger = logging.getLogger(__name__)


class FileStorageBackend(ABC):
    """Abstract interface for storing and retrieving uploaded worksheet images."""

    @abstractmethod
    def save_file(
        self,
        org_id: str,
        assessment_id: str,
        filename: str,
        content: bytes,
        mime_type: str = "image/jpeg",
    ) -> str:
        """Saves file content and returns the canonical stored filename or URI."""
        ...

    @abstractmethod
    def get_file_bytes(
        self,
        org_id: str,
        assessment_id: str,
        filename: str,
    ) -> Optional[Tuple[bytes, str]]:
        """Retrieves raw file bytes and mime type, or None if not found."""
        ...

    @abstractmethod
    def file_exists(
        self,
        org_id: str,
        assessment_id: str,
        filename: str,
    ) -> bool:
        """Checks if the file exists in storage."""
        ...


class LocalFilesystemStorage(FileStorageBackend):
    """Stores files on the local filesystem partitioned by tenant and assessment."""

    def __init__(self, base_dir: Optional[Path] = None):
        self._base_dir = base_dir

    @property
    def base_dir(self) -> Path:
        return self._base_dir or get_uploads_dir()

    def _get_target_path(self, org_id: str, assessment_id: str, filename: str) -> Path:
        safe_org = re.sub(r"[^a-zA-Z0-9_-]", "_", org_id)
        safe_asm = re.sub(r"[^a-zA-Z0-9_-]", "_", assessment_id)
        safe_filename = os.path.basename(filename)
        return self.base_dir / safe_org / safe_asm / safe_filename

    def save_file(
        self,
        org_id: str,
        assessment_id: str,
        filename: str,
        content: bytes,
        mime_type: str = "image/jpeg",
    ) -> str:
        target_path = self._get_target_path(org_id, assessment_id, filename)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(content)
        return target_path.name

    def get_file_bytes(
        self,
        org_id: str,
        assessment_id: str,
        filename: str,
    ) -> Optional[Tuple[bytes, str]]:
        target_path = self._get_target_path(org_id, assessment_id, filename)
        if not target_path.is_file():
            # Check fallback search in tenant upload root
            safe_org = re.sub(r"[^a-zA-Z0-9_-]", "_", org_id)
            alt = self.base_dir / safe_org / os.path.basename(filename)
            if alt.is_file():
                target_path = alt
            else:
                return None
        with open(target_path, "rb") as f:
            data = f.read()
        return data, "image/jpeg"

    def file_exists(
        self,
        org_id: str,
        assessment_id: str,
        filename: str,
    ) -> bool:
        target_path = self._get_target_path(org_id, assessment_id, filename)
        if target_path.is_file():
            return True
        safe_org = re.sub(r"[^a-zA-Z0-9_-]", "_", org_id)
        alt = self.base_dir / safe_org / os.path.basename(filename)
        return alt.is_file()


class GoogleCloudStorageBackend(FileStorageBackend):
    """Stores files in a private Google Cloud Storage bucket with IAM authorization."""

    def __init__(self, bucket_name: str, client=None):
        self.bucket_name = bucket_name
        self._client = client
        self._bucket = None
        if client is not None:
            self._bucket = client.bucket(bucket_name)

    def _get_bucket(self):
        if self._bucket is None:
            from google.cloud import storage

            self._client = storage.Client(project=settings.google_cloud_project)
            self._bucket = self._client.bucket(self.bucket_name)
        return self._bucket

    def _blob_name(self, org_id: str, assessment_id: str, filename: str) -> str:
        safe_org = re.sub(r"[^a-zA-Z0-9_-]", "_", org_id)
        safe_asm = re.sub(r"[^a-zA-Z0-9_-]", "_", assessment_id)
        safe_filename = os.path.basename(filename)
        return f"uploads/{safe_org}/{safe_asm}/{safe_filename}"

    def save_file(
        self,
        org_id: str,
        assessment_id: str,
        filename: str,
        content: bytes,
        mime_type: str = "image/jpeg",
    ) -> str:
        blob_name = self._blob_name(org_id, assessment_id, filename)
        bucket = self._get_bucket()
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content, content_type=mime_type)
        logger.info(f"Saved file to GCS: gs://{self.bucket_name}/{blob_name}")
        return os.path.basename(filename)

    def get_file_bytes(
        self,
        org_id: str,
        assessment_id: str,
        filename: str,
    ) -> Optional[Tuple[bytes, str]]:
        blob_name = self._blob_name(org_id, assessment_id, filename)
        bucket = self._get_bucket()
        blob = bucket.blob(blob_name)
        if not blob.exists():
            return None
        data = blob.download_as_bytes()
        mime_type = blob.content_type or "image/jpeg"
        return data, mime_type

    def file_exists(
        self,
        org_id: str,
        assessment_id: str,
        filename: str,
    ) -> bool:
        blob_name = self._blob_name(org_id, assessment_id, filename)
        bucket = self._get_bucket()
        blob = bucket.blob(blob_name)
        return blob.exists()


_file_storage: Optional[FileStorageBackend] = None


def get_file_storage() -> FileStorageBackend:
    """Returns the singleton storage backend based on runtime configuration."""
    global _file_storage
    if _file_storage is None:
        bucket = os.getenv("CLASSLENS_GCS_BUCKET")
        if bucket and not os.environ.get("PYTEST_CURRENT_TEST"):
            try:
                _file_storage = GoogleCloudStorageBackend(bucket_name=bucket)
                logger.info("Initialized GoogleCloudStorageBackend with bucket '%s'", bucket)
            except Exception as e:
                logger.warning(
                    "Could not initialize GCS backend: %s. Falling back to LocalFilesystemStorage.", e
                )
                _file_storage = LocalFilesystemStorage()
        else:
            _file_storage = LocalFilesystemStorage()
    return _file_storage


def reset_file_storage() -> None:
    """Resets the singleton storage backend (used in tests)."""
    global _file_storage
    _file_storage = None
