"""Modular manuscript rendering cache for fast incremental compilation."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_SCHEMA_VERSION = 1


class RenderCacheError(ValueError):
    """Raised when the persistent render cache cannot be trusted or saved."""


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
            "rendered_outputs": list(self.rendered_outputs),
            "timestamp": self.timestamp,
        }


class ManuscriptRenderCache:
    """File-backed incremental rendering cache."""

    def __init__(self, cache_file: Path | str) -> None:
        self.cache_file = Path(cache_file)
        self._cache_root = self.cache_file.parent.resolve()
        self._entries: dict[str, SectionCacheEntry] = {}
        self._load()

    def _load(self) -> None:
        """Load cache entries from JSON file."""
        if not self.cache_file.exists():
            return
        try:
            payload = json.loads(self.cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RenderCacheError(f"Invalid render cache JSON at {self.cache_file}: {exc.msg}") from exc
        except OSError as exc:
            raise RenderCacheError(f"Could not read render cache {self.cache_file}: {exc}") from exc

        if not isinstance(payload, dict) or payload.get("schema_version") != _SCHEMA_VERSION:
            raise RenderCacheError(
                f"Unsupported render cache schema at {self.cache_file}; expected version {_SCHEMA_VERSION}"
            )
        raw_entries = payload.get("entries")
        if not isinstance(raw_entries, list):
            raise RenderCacheError(f"Render cache entries must be a list: {self.cache_file}")

        entries: dict[str, SectionCacheEntry] = {}
        for index, item in enumerate(raw_entries):
            if not isinstance(item, dict):
                raise RenderCacheError(f"Render cache entry {index} is not an object: {self.cache_file}")
            file_name = item.get("file_name")
            content_hash = item.get("content_hash")
            rendered_outputs = item.get("rendered_outputs")
            timestamp = item.get("timestamp")
            if not isinstance(file_name, str) or not file_name:
                raise RenderCacheError(f"Render cache entry {index} has no valid file key: {self.cache_file}")
            if (
                not isinstance(content_hash, str)
                or len(content_hash) != 64
                or content_hash != content_hash.lower()
                or any(character not in "0123456789abcdef" for character in content_hash)
            ):
                raise RenderCacheError(f"Render cache entry {index} has an invalid content hash: {self.cache_file}")
            if not isinstance(rendered_outputs, list) or not all(isinstance(path, str) for path in rendered_outputs):
                raise RenderCacheError(f"Render cache entry {index} has invalid rendered outputs: {self.cache_file}")
            if (
                isinstance(timestamp, bool)
                or not isinstance(timestamp, (int, float))
                or not math.isfinite(timestamp)
                or timestamp < 0
            ):
                raise RenderCacheError(f"Render cache entry {index} has an invalid timestamp: {self.cache_file}")
            if file_name in entries:
                raise RenderCacheError(f"Duplicate render cache key {file_name!r}: {self.cache_file}")
            entries[file_name] = SectionCacheEntry(
                file_name=file_name,
                content_hash=content_hash,
                rendered_outputs=list(rendered_outputs),
                timestamp=float(timestamp),
            )
        self._entries = entries

    def save(self) -> None:
        """Persist cache entries to disk atomically."""
        payload = {
            "schema_version": _SCHEMA_VERSION,
            "entries": [entry.to_dict() for entry in sorted(self._entries.values(), key=lambda item: item.file_name)],
        }
        tmp_path: Path | None = None
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.cache_file.parent,
                delete=False,
                suffix=".tmp",
            ) as handle:
                tmp_path = Path(handle.name)
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            tmp_path.replace(self.cache_file)
        except (OSError, TypeError, ValueError) as exc:
            raise RenderCacheError(f"Could not save render cache {self.cache_file}: {exc}") from exc
        finally:
            if tmp_path is not None:
                try:
                    tmp_path.unlink(missing_ok=True)
                except OSError:
                    pass

    @staticmethod
    def compute_hash(file_path: Path) -> str:
        """Calculate SHA-256 hash of a source file."""
        try:
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except OSError:
            return ""

    def is_up_to_date(self, source_file: Path, expected_outputs: list[Path]) -> bool:
        """Check hash, exact output set, and file outputs for a cached section."""
        entry = self._entries.get(self._path_key(source_file))
        if not entry:
            return False
        current_hash = self.compute_hash(source_file)
        if not current_hash or current_hash != entry.content_hash:
            return False
        expected_keys = [self._path_key(output) for output in expected_outputs]
        if expected_keys != entry.rendered_outputs:
            return False
        return all(output.is_file() for output in expected_outputs)

    def record_rendered(self, source_file: Path, outputs: list[Path]) -> None:
        """Record successful render of a section."""
        content_hash = self.compute_hash(source_file)
        if not content_hash:
            raise RenderCacheError(f"Cannot cache missing or unreadable source file: {source_file}")
        if not all(output.is_file() for output in outputs):
            raise RenderCacheError("Cannot cache a render with missing or non-file outputs")
        key = self._path_key(source_file)
        self._entries[key] = SectionCacheEntry(
            file_name=key,
            content_hash=content_hash,
            rendered_outputs=[self._path_key(output) for output in outputs],
            timestamp=time.time(),
        )
        self.save()

    def clear(self) -> None:
        """Clear the cache."""
        self._entries.clear()
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except OSError as exc:
                raise RenderCacheError(f"Could not clear render cache {self.cache_file}: {exc}") from exc

    def _path_key(self, path: Path) -> str:
        """Return a collision-resistant cache key for a source or output path."""
        resolved = Path(path).resolve()
        try:
            return resolved.relative_to(self._cache_root).as_posix()
        except ValueError:
            return f"external:{resolved.as_posix()}"


__all__ = [
    "ManuscriptRenderCache",
    "RenderCacheError",
    "SectionCacheEntry",
]
