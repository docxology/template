"""Invariants for docs/documentation-index.md (signposting and audit commands)."""

from __future__ import annotations

from pathlib import Path


def test_documentation_index_links_operational_build_and_audit_orchestrator() -> None:
    repo = Path(__file__).resolve().parents[2]
    text = (repo / "docs" / "documentation-index.md").read_text(encoding="utf-8")
    assert "operational/build/build-system.md" in text
    assert "scripts/audit_filepaths.py" in text
