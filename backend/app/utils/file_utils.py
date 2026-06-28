"""
File utilities - validation, hashing, path helpers.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional


def compute_file_hash(content: bytes) -> str:
    """SHA-256 hash of file bytes."""
    return hashlib.sha256(content).hexdigest()


def validate_file(filename: str, content: bytes, max_mb: int) -> Optional[str]:
    """
    Validate file type and size.
    Returns error message string, or None if valid.
    """
    ext = Path(filename).suffix.lower()
    allowed = {".pdf", ".docx", ".txt", ".md"}
    if ext not in allowed:
        return f"File type '{ext}' not allowed. Supported: {sorted(allowed)}"

    size_mb = len(content) / (1024 * 1024)
    if size_mb > max_mb:
        return f"File size {size_mb:.1f}MB exceeds limit of {max_mb}MB"

    return None


def safe_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    name = Path(filename).name
    name = "".join(c for c in name if c.isalnum() or c in "._- ")
    return name[:255]
