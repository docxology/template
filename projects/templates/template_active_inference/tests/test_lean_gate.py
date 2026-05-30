"""Lean build gate tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from gates.validation import build_lean, lean_project_present


@pytest.mark.skipif(shutil.which("lake") is None, reason="lake toolchain not installed")
def test_build_lean_when_present_must_succeed() -> None:
    root = Path(__file__).resolve().parents[1]
    assert lean_project_present(root)
    code, msg = build_lean(root)
    assert code == 0, msg


def test_build_lean_skips_without_lakefile(tmp_path: Path) -> None:
    assert not lean_project_present(tmp_path)
    code, msg = build_lean(tmp_path)
    assert code == 0
    assert "skipped" in msg.lower()
