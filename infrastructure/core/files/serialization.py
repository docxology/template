"""Shared filesystem read + path helpers (R6 de-duplication).

Consolidates three helper bodies that previously lived verbatim across several
infrastructure modules (reporting, pipeline, documentation, project/drift):

* :func:`read_json_object` — parse a JSON file into a mapping, returning ``{}``
  when the file is absent, unreadable, or not a JSON object.
* :func:`load_yaml_mapping` — parse a YAML file into a mapping, returning ``{}``
  when the file is absent or not a YAML mapping.
* :func:`relative_or_self` — best-effort ``path.relative_to(base)`` as a string,
  falling back to ``str(path)`` when *path* is outside *base*.

All three are pure/deterministic and never raise on missing or malformed input.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = ["load_yaml_mapping", "read_json_object", "relative_or_self"]


def read_json_object(path: Path) -> dict[str, Any]:
    """Return the JSON object at *path*, or ``{}`` when absent/unreadable/non-object."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    """Return the YAML mapping at *path*, or ``{}`` when absent/non-mapping."""
    if not path.is_file():
        return {}
    import yaml  # noqa: PLC0415 — keep import cost off callers that never load YAML

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def relative_or_self(path: Path, base: Path) -> str:
    """Return ``str(path.relative_to(base))``, falling back to ``str(path)`` if outside *base*."""
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)
