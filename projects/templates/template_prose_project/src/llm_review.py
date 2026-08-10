"""Offline-first contracts for optional language-model review evidence.

This module deliberately contains no model client and no network code. A
fork may run an explicitly configured provider elsewhere, but it must leave a
deterministic transcript receipt that this base exemplar can validate.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .config import LLMReviewConfig

LLM_REVIEW_SCHEMA_VERSION = "template-prose/llm-review/1"
LLM_TRANSCRIPT_SCHEMA_VERSION = "template-prose/llm-transcript/1"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_TRANSCRIPT_KEYS = frozenset(
    {
        "schema_version",
        "provider",
        "model",
        "prompt_digest",
        "response_digest",
        "reviewer",
        "reviewed_paths",
        "status",
    }
)


def _canonical_digest(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _safe_transcript_path(root: Path, configured: str) -> Path:
    base = root.resolve()
    path = (base / configured).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"LLM transcript path escapes project root: {configured!r}") from exc
    return path


def validate_transcript(payload: dict[str, Any]) -> None:
    """Validate the exact, portable transcript schema used by the receipt."""
    unknown = sorted(set(payload) - _TRANSCRIPT_KEYS)
    missing = sorted(_TRANSCRIPT_KEYS - set(payload))
    if unknown or missing:
        raise ValueError(f"LLM transcript schema mismatch: missing={missing}, unknown={unknown}")
    if payload["schema_version"] != LLM_TRANSCRIPT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported LLM transcript schema: {payload['schema_version']!r}")
    if payload["status"] != "completed":
        raise ValueError(f"LLM transcript must have status 'completed', got {payload['status']!r}")
    for key in ("provider", "model", "reviewer"):
        if not isinstance(payload[key], str) or not payload[key].strip():
            raise ValueError(f"LLM transcript field {key!r} must be a non-empty string")
    for key in ("prompt_digest", "response_digest"):
        if not isinstance(payload[key], str) or not _DIGEST_RE.fullmatch(payload[key]):
            raise ValueError(f"LLM transcript field {key!r} must be a lowercase SHA-256 digest")
    paths = payload["reviewed_paths"]
    if not isinstance(paths, list) or not paths or any(not isinstance(path, str) for path in paths):
        raise ValueError("LLM transcript reviewed_paths must be a non-empty list of strings")
    for path in paths:
        candidate = Path(path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"LLM transcript reviewed path is unsafe: {path!r}")


def build_llm_review_receipt(config: LLMReviewConfig, *, project_root: Path | str) -> dict[str, object]:
    """Return a deterministic receipt, or an explicit disabled skip.

    Enabled reviews remain transcript-only at this layer. No provider is
    contacted, so network and live-model behaviour cannot become an implicit
    dependency of the public exemplar.
    """
    if not config.enabled:
        return {
            "schema_version": LLM_REVIEW_SCHEMA_VERSION,
            "status": "skipped",
            "reason": "disabled_by_config",
        }
    transcript_path = _safe_transcript_path(Path(project_root), config.transcript_path)
    if not transcript_path.is_file():
        raise ValueError(f"enabled LLM review requires transcript receipt: {transcript_path}")
    try:
        payload = json.loads(transcript_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM transcript is not valid JSON: {transcript_path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("LLM transcript must be a JSON object")
    validate_transcript(payload)
    if payload["provider"] != config.provider or payload["model"] != config.model:
        raise ValueError("LLM transcript provider/model does not match configured review")
    return {
        "schema_version": LLM_REVIEW_SCHEMA_VERSION,
        "status": "verified",
        "execution": "transcript_only",
        "provider": config.provider,
        "model": config.model,
        "transcript_path": config.transcript_path,
        "transcript_digest": _canonical_digest(payload),
        "reviewed_paths": payload["reviewed_paths"],
    }


__all__ = [
    "LLM_REVIEW_SCHEMA_VERSION",
    "LLM_TRANSCRIPT_SCHEMA_VERSION",
    "build_llm_review_receipt",
    "validate_transcript",
]
