"""Content-idempotent writes for compiled manuscript source."""

from __future__ import annotations

from pathlib import Path


def write_compiled_text(path: Path, content: str) -> Path:
    """Preserve physical source custody when compilation yields identical bytes."""
    encoded = content.encode("utf-8")
    if path.is_file() and path.read_bytes() == encoded:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    return path
