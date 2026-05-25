#!/usr/bin/env python3
"""Audit pandoc-crossref-style section/table identifiers in manuscript fragments."""

from __future__ import annotations

import re
from pathlib import Path

_DEF_RE = re.compile(r"\{#([a-zA-Z0-9:_-]+)\}")
_REF_RE = re.compile(r"@(?P<kind>sec|tbl|fig|eq):(?P<label>[a-zA-Z0-9:_-]+)")


def _collect_markdown_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def audit(manuscript_dir: Path) -> int:
    """Return 0 when identifiers are consistent; 1 when orphans or duplicates exist."""
    defined: dict[str, Path] = {}
    references: list[tuple[str, Path]] = []
    errors = 0

    for md_path in _collect_markdown_files(manuscript_dir):
        text = md_path.read_text(encoding="utf-8")
        for match in _DEF_RE.finditer(text):
            label = match.group(1)
            if label in defined:
                errors += 1
            else:
                defined[label] = md_path
        for match in _REF_RE.finditer(text):
            references.append((f"{match.group('kind')}:{match.group('label')}", md_path))

    for label, ref_path in references:
        if label not in defined:
            errors += 1

    return 1 if errors else 0
