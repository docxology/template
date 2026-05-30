"""Standalone PDF rendering helpers.

Self-contained — no monorepo ``infrastructure`` import. Used by
``scripts/render_pdf.py`` (standalone portable build) and testable in
isolation.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


def extract_preamble(preamble_md: Path) -> str:
    """Return the LaTeX inside the ```latex fence of preamble.md (or "")."""
    if not preamble_md.is_file():
        return ""
    blocks = re.findall(
        r"```\s*latex\s*\n(.*?)\n\s*```",
        preamble_md.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    return "\n".join(b.strip() for b in blocks)


def geometry_string(config_yaml: Path) -> str:
    """Read page geometry from ``manuscript/config.yaml``; fall back to 0.5 in margins."""
    if not config_yaml.is_file():
        return "margin=0.5in"
    data = yaml.safe_load(config_yaml.read_text(encoding="utf-8")) or {}
    return str((data.get("metadata") or {}).get("geometry") or "margin=0.5in")
