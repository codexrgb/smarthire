"""
Private file storage interface for resume documents.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from src.backend.config import settings


def sanitize_filename(filename: str) -> str:
    """Removes path separators, directory components, and dangerous characters from filenames."""
    if not filename:
        return "document.txt"
    # Strip null bytes first
    cleaned = filename.replace("\x00", "")
    # Extract basename to eliminate directory traversal components
    basename = Path(cleaned).name
    basename = basename.split("\\")[-1].split("/")[-1]
    # Keep only alphanumeric, dot, underscore, dash
    clean = re.sub(r"[^a-zA-Z0-9._-]", "_", basename)
    clean = re.sub(r"^\.+", "", clean)  # remove leading dots
    return clean or "document.txt"


class PrivateFileStorage:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = (base_dir or settings.STORAGE_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, storage_path: str) -> Path:
        """Validates that a path is strictly contained within the private storage root."""
        target = Path(storage_path).resolve()
        try:
            target.relative_to(self.base_dir)
        except ValueError:
            raise PermissionError(
                f"Access denied: Path traversal detected outside storage root: {storage_path}"
            )
        return target

    def save_file(self, content: bytes, original_filename: str) -> Dict[str, Any]:
        """
        Saves raw resume bytes to private storage using SHA-256 deduplicated subdirectories.
        Prevents directory traversal and logs only metadata (never raw text).
        """
        sha256_hash = hashlib.sha256(content).hexdigest()
        clean_name = sanitize_filename(original_filename)

        # Structure by first 2 chars of hash to prevent large flat directories
        sub_dir = self.base_dir / sha256_hash[:2]
        sub_dir.mkdir(parents=True, exist_ok=True)

        target_path = sub_dir / f"{sha256_hash}_{clean_name}"
        with open(target_path, "wb") as f:
            f.write(content)

        return {
            "storage_path": str(target_path),
            "sha256": sha256_hash,
            "size_bytes": len(content),
            "original_filename": clean_name
        }

    def get_file(self, storage_path: str) -> bytes:
        """Retrieves raw file bytes from storage path after verifying path containment."""
        safe_path = self._resolve_safe_path(storage_path)
        if not safe_path.exists():
            raise FileNotFoundError(f"File not found in storage: {storage_path}")
        with open(safe_path, "rb") as f:
            return f.read()

    def delete_file(self, storage_path: str) -> bool:
        """Deletes file from storage after verifying path containment."""
        safe_path = self._resolve_safe_path(storage_path)
        if safe_path.exists():
            safe_path.unlink()
            return True
        return False


storage_service = PrivateFileStorage()
