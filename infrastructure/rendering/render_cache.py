"""Modular manuscript rendering cache for fast incremental compilation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SectionCacheEntry:
    """Cache record for a single rendered manuscript section."""

    file_name: str
    content_hash: str
    rendered_outputs: list[str] = field(default_factory=list)
    timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert entry to JSON-safe dictionary."""
        return {
            "file_name": self.file_name,
            "content_hash": self.content_hash,
            "rendered_outputs": self.rendered_outputs,
            "timestamp": self.timestamp,
        }


class ManuscriptRenderCache:
    """File-backed incremental rendering cache."""

    def __init__(self, cache_file: Path | str) -> None:
        self.cache_file = Path(cache_file)
        self._entries: dict[str, SectionCacheEntry] = {}
        self._load()

    def _load(self) -> None:
        """Load cache entries from JSON file."""
        if not self.cache_file.exists():
            return
        try:
            payload = json.loads(self.cache_file.read_text(encoding="utf-8"))
            for item in payload.get("entries", []):
                entry = SectionCacheEntry(
                    file_name=item["file_name"],
                    content_hash=item["content_hash"],
                    rendered_outputs=item.get("rendered_outputs", []),
                    timestamp=item.get("timestamp", 0.0),
                )
                self._entries[entry.file_name] = entry
        except (OSError, json.JSONDecodeError):
            self._entries.clear()

    def save(self) -> None:
        """Persist cache entries to disk atomically."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "entries": [entry.to_dict() for entry in self._entries.values()],
        }
        tmp_path = self.cache_file.with_suffix(".tmp")
        try:
            tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp_path.replace(self.cache_file)
        except OSError:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    @staticmethod
    def compute_hash(file_path: Path) -> str:
        """Calculate SHA-256 hash of a source file."""
        try:
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except OSError:
            return ""

    def is_up_to_date(self, source_file: Path, expected_outputs: list[Path]) -> bool:
        """Check if source file matches cached hash and all output files exist."""
        entry = self._entries.get(source_file.name)
        if not entry:
            return False
        current_hash = self.compute_hash(source_file)
        if not current_hash or current_hash != entry.content_hash:
            return False
        return all(out.exists() for out in expected_outputs)

    def record_rendered(self, source_file: Path, outputs: list[Path]) -> None:
        """Record successful render of a section."""
        content_hash = self.compute_hash(source_file)
        self._entries[source_file.name] = SectionCacheEntry(
            file_name=source_file.name,
            content_hash=content_hash,
            rendered_outputs=[str(p) for p in outputs],
        )
        self.save()

    def clear(self) -> None:
        """Clear the cache."""
        self._entries.clear()
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except OSError:
                pass


__all__ = [
    "ManuscriptRenderCache",
    "SectionCacheEntry",
]
