"""Offline transcript envelope and stale-replay checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


TRANSCRIPT_SCHEMA = "template-autoscientists/transcript/1"


def transcript_digest(payload: dict[str, Any]) -> str:
    """Return a stable digest over transcript content and metadata."""
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_transcript(
    payload: Any,
    *,
    expected_revision: str | None = None,
    require_offline: bool = True,
) -> list[str]:
    """Return actionable errors for a replayable transcript envelope."""
    if not isinstance(payload, dict):
        return ["transcript must be a mapping"]
    issues: list[str] = []
    if payload.get("schema_version") != TRANSCRIPT_SCHEMA:
        issues.append(f"schema_version must be {TRANSCRIPT_SCHEMA}")
    revision = str(payload.get("revision", "")).strip()
    if not revision:
        issues.append("revision must be non-empty")
    elif expected_revision is not None and revision != expected_revision:
        issues.append(f"stale transcript revision: expected {expected_revision}, got {revision}")
    mode = str(payload.get("mode", "")).strip().lower()
    if require_offline and mode != "offline":
        issues.append("offline replay requires mode=offline")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        issues.append("entries must be a non-empty list")
    else:
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                issues.append(f"entries[{index}] must be a mapping")
                continue
            if not str(entry.get("role", "")).strip() or not str(entry.get("content", "")).strip():
                issues.append(f"entries[{index}] requires role and content")
    return issues


def replay_transcript(path: Path | str, *, expected_revision: str) -> list[dict[str, str]]:
    """Load a transcript only after schema/revision/offline validation."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    issues = validate_transcript(payload, expected_revision=expected_revision)
    if issues:
        raise ValueError(f"Invalid transcript: {issues}")
    return [{"role": str(entry["role"]), "content": str(entry["content"])} for entry in payload["entries"]]


__all__ = ["TRANSCRIPT_SCHEMA", "replay_transcript", "transcript_digest", "validate_transcript"]
