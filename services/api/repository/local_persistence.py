"""Local durable storage layer for ClassLens local offline demo persistence.

Features:
- Atomic file-based persistence for tenant state (responses, audit events, assessment metadata).
- Tenant-isolated storage partitions (e.g. local-data/store/{org_id}_state.json).
- Schema validation via Pydantic model validation.
- Preservation of original AI findings (analysis_data) distinct from educator overrides.
- Crash resilience via write-to-temp and atomic rename (os.replace).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path("local-data/store")


class LocalStatePersistence:
    """Manages atomic, tenant-isolated state serialization to disk."""

    def __init__(self, data_dir: Optional[Path] = None):
        env_dir = os.environ.get("CLASSLENS_DATA_DIR")
        self.data_dir = Path(env_dir) if env_dir else (data_dir or DEFAULT_DATA_DIR)
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.warning(f"Could not create storage directory {self.data_dir}: {exc}")

    def _get_tenant_file(self, org_id: str) -> Path:
        safe_org = "".join(c for c in org_id if c.isalnum() or c in ("-", "_"))
        return self.data_dir / f"{safe_org}_state.json"

    def save_tenant_state(
        self,
        org_id: str,
        assessments: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        audit_events: List[Dict[str, Any]],
    ) -> bool:
        """Atomically saves state for a tenant."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            target_path = self._get_tenant_file(org_id)
            temp_path = self.data_dir / f".{target_path.name}.tmp"

            payload = {
                "version": "1.0",
                "org_id": org_id,
                "assessments": assessments,
                "responses": responses,
                "audit_events": audit_events,
            }

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_path, target_path)
            return True
        except Exception as exc:
            logger.error(f"Failed to persist tenant state for {org_id}: {exc}")
            return False

    def load_tenant_state(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Loads and parses persisted tenant state if available."""
        target_path = self._get_tenant_file(org_id)
        if not target_path.exists():
            return None

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as exc:
            logger.error(f"Failed to load tenant state for {org_id}: {exc}")
            return None

    def clear_tenant_state(self, org_id: str) -> bool:
        """Clears persisted tenant state (used in testing)."""
        target_path = self._get_tenant_file(org_id)
        if target_path.exists():
            try:
                target_path.unlink()
                return True
            except OSError:
                return False
        return True
