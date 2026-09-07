"""Transmission bookend validation for the generated manuscript payload."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

BOOKEND_SCHEMA_VERSION = 1
BEGIN_BOOKEND = "00_000_transmission_begin.md"
END_BOOKEND = "99_999_transmission_end.md"
_DOC_ONLY = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})


def _file_record(path: Path, role: str) -> dict[str, Any]:
    content = path.read_bytes()
    return {
        "role": role,
        "path": f"manuscript/{path.name}",
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }


def validate_transmission_bookends(manuscript_dir: str | Path) -> dict[str, Any]:
    """Return a typed receipt or fail when the manuscript is not bookended."""
    root = Path(manuscript_dir)
    source_files = sorted(
        path for path in root.glob("*.md") if path.name not in _DOC_ONLY and path.name != "preamble.md"
    )
    if not source_files:
        raise ValueError("manuscript has no source sections")
    if source_files[0].name != BEGIN_BOOKEND:
        raise ValueError(f"first manuscript section must be {BEGIN_BOOKEND}")
    if source_files[-1].name != END_BOOKEND:
        raise ValueError(f"last manuscript section must be {END_BOOKEND}")
    begin_text = source_files[0].read_text(encoding="utf-8")
    end_text = source_files[-1].read_text(encoding="utf-8")
    if "<!-- transmission:begin -->" not in begin_text:
        raise ValueError("transmission begin bookend marker is missing")
    if "<!-- transmission:end -->" not in end_text:
        raise ValueError("transmission end bookend marker is missing")
    return {
        "schema_version": BOOKEND_SCHEMA_VERSION,
        "status": "pass",
        "first_section": _file_record(source_files[0], "transmission_begin"),
        "last_section": _file_record(source_files[-1], "transmission_end"),
        "section_count": len(source_files),
    }


__all__ = ["BEGIN_BOOKEND", "BOOKEND_SCHEMA_VERSION", "END_BOOKEND", "validate_transmission_bookends"]
