"""Load and save local continual-learning agent memory (gitignored JSON)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MEMORY_REL_PATH = Path(".cursor/hooks/state/continual-learning-memory.json")
EXAMPLE_REL_PATH = Path(".cursor/hooks/state/continual-learning-memory.example.json")
MAX_BULLETS = 12

_REQUIRED_KEYS = ("version", "updated_at", "learned_user_preferences", "learned_workspace_facts")


def memory_path(repo_root: Path) -> Path:
    """Return the live memory file path under ``repo_root``."""
    return repo_root / MEMORY_REL_PATH


def example_path(repo_root: Path) -> Path:
    """Return the tracked schema example path under ``repo_root``."""
    return repo_root / EXAMPLE_REL_PATH


def normalize_bullets(items: list[str], *, max_items: int = MAX_BULLETS) -> list[str]:
    """Strip, drop empties, dedupe case-insensitively, and cap list length."""
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in items:
        bullet = raw.strip()
        if not bullet:
            continue
        key = bullet.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(bullet)
        if len(normalized) >= max_items:
            break
    return normalized


def _validate_payload(payload: dict[str, Any]) -> None:
    missing = [key for key in _REQUIRED_KEYS if key not in payload]
    if missing:
        raise ValueError(f"memory payload missing keys: {', '.join(missing)}")
    if payload["version"] != 1:
        raise ValueError(f"unsupported memory version: {payload['version']!r}")
    for field in ("learned_user_preferences", "learned_workspace_facts"):
        value = payload[field]
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"{field} must be a list of strings")


def empty_memory_payload() -> dict[str, Any]:
    """Return a fresh version-1 memory document."""
    return {
        "version": 1,
        "updated_at": None,
        "learned_user_preferences": [],
        "learned_workspace_facts": [],
    }


def load_memory(repo_root: Path) -> dict[str, Any]:
    """Load memory JSON, or the example schema when the live file is absent."""
    path = memory_path(repo_root)
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        example = example_path(repo_root)
        if example.is_file():
            payload = json.loads(example.read_text(encoding="utf-8"))
        else:
            payload = empty_memory_payload()
    _validate_payload(payload)
    payload["learned_user_preferences"] = normalize_bullets(payload["learned_user_preferences"])
    payload["learned_workspace_facts"] = normalize_bullets(payload["learned_workspace_facts"])
    return payload


def save_memory(repo_root: Path, payload: dict[str, Any]) -> Path:
    """Validate, normalize, and write memory JSON; return the written path."""
    _validate_payload(payload)
    payload = dict(payload)
    payload["learned_user_preferences"] = normalize_bullets(payload["learned_user_preferences"])
    payload["learned_workspace_facts"] = normalize_bullets(payload["learned_workspace_facts"])
    payload["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
    path = memory_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
