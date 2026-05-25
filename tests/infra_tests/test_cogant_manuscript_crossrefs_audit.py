"""Tests for COGANT ``audit_manuscript_crossrefs.py``.

Ensures pandoc-crossref-style ``@sec:`` / ``{#sec:`` identifiers stay internally
consistent across COGANT manuscript fragments (staging or committed fixture).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from tests.infra_tests._cogant_paths import cogant_root

pytestmark = pytest.mark.private_project

_COGANT = cogant_root()
_SCRIPT = _COGANT / "tools/audit_manuscript_crossrefs.py"
_MANUSCRIPT_DIR = _COGANT / "manuscript"


def _load_audit_module():
    if not _SCRIPT.is_file():
        pytest.fail(f"COGANT audit script not present: {_SCRIPT}")
    spec = importlib.util.spec_from_file_location("audit_manuscript_crossrefs", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_audit_manuscript_crossrefs_passes_on_staging_tree() -> None:
    """Staging manuscript must have no orphan @sec/@tbl refs or duplicate {#…} ids."""
    mod = _load_audit_module()
    if not _MANUSCRIPT_DIR.is_dir():
        pytest.fail(f"COGANT manuscript dir not present: {_MANUSCRIPT_DIR}")
    assert mod.audit(_MANUSCRIPT_DIR) == 0


def test_audit_detects_orphan_reference(tmp_path: Path) -> None:
    mod = _load_audit_module()
    md = tmp_path / "01_x.md"
    md.write_text("# x {#sec:01-x}\nSee @sec:missing-label.\n", encoding="utf-8")
    assert mod.audit(tmp_path) == 1


def test_audit_detects_duplicate_definition(tmp_path: Path) -> None:
    mod = _load_audit_module()
    (tmp_path / "a.md").write_text("# A {#sec:same}\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("# B {#sec:same}\n", encoding="utf-8")
    assert mod.audit(tmp_path) == 1
