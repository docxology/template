"""Direct tests for ``gates.lean`` that do not require a Lean toolchain.

``test_lean_gate.py`` exercises the real ``lake`` build when the toolchain is
installed; CI images do not ship it, so the subprocess and axiom-parsing paths
had no leg-deterministic coverage. These tests drive them with a scripted
``lake`` stand-in on ``PATH`` — a real subprocess with test-scripted responses,
the CLI analogue of the repo's sanctioned ``pytest-httpserver`` pattern (no
mock objects; the production code path runs unmodified end to end).
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from gates.lean import build_lean, lean_axioms_clean, lean_project_present

_STUB_SCRIPT = """#!/bin/sh
mode="${LAKE_STUB_MODE:-build_ok}"
case "$mode" in
  build_ok)
    echo "stub lake build completed"
    exit 0
    ;;
  build_fail)
    echo "stub lake build error: unsolved goals" >&2
    exit 1
    ;;
  axioms_clean)
    echo "'TemplateActiveInference.thm' depends on axioms: [propext, Classical.choice, Quot.sound]"
    exit 0
    ;;
  axioms_sorry)
    echo "'TemplateActiveInference.thm' depends on axioms: [sorryAx]"
    exit 0
    ;;
  axioms_native)
    echo "'TemplateActiveInference.thm' depends on axioms: [Lean.ofReduceBool]"
    exit 0
    ;;
  axioms_error)
    echo "elaboration failed" >&2
    exit 1
    ;;
esac
"""


@pytest.fixture
def lean_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A minimal Lake project plus a scripted ``lake`` executable on PATH."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "lake"
    stub.write_text(_STUB_SCRIPT, encoding="utf-8")
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")

    root = tmp_path / "project"
    module_dir = root / "lean" / "TemplateActiveInference"
    module_dir.mkdir(parents=True)
    (root / "lean" / "lakefile.lean").write_text("package template\n", encoding="utf-8")
    (module_dir / "Basic.lean").write_text(
        "import TemplateActiveInference.Other\ntheorem thm : True := trivial\n",
        encoding="utf-8",
    )
    return root


def test_lean_project_present_detects_lakefile(lean_root: Path, tmp_path: Path) -> None:
    assert lean_project_present(lean_root) is True
    assert lean_project_present(tmp_path / "empty") is False


def test_build_lean_skips_cleanly_when_project_absent(tmp_path: Path) -> None:
    code, message = build_lean(tmp_path)
    assert code == 0
    assert "skipped" in message


def test_build_lean_returns_stub_output_on_success(lean_root: Path) -> None:
    code, message = build_lean(lean_root)
    assert code == 0
    assert "stub lake build completed" in message


def test_build_lean_propagates_nonzero_exit(lean_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LAKE_STUB_MODE", "build_fail")
    code, message = build_lean(lean_root)
    assert code == 1
    assert "unsolved goals" in message


def test_lean_axioms_clean_skips_when_project_absent(tmp_path: Path) -> None:
    ok, message = lean_axioms_clean(tmp_path)
    assert ok is True
    assert "skipped" in message


def test_lean_axioms_clean_accepts_whitelisted_axioms(lean_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LAKE_STUB_MODE", "axioms_clean")
    ok, message = lean_axioms_clean(lean_root, declarations=("TemplateActiveInference.thm",))
    assert ok is True
    assert "depends on axioms" in message
    assert not (lean_root / "lean" / "_AxiomCheck.lean").exists(), "checker file must be cleaned up"


def test_lean_axioms_clean_rejects_sorry(lean_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LAKE_STUB_MODE", "axioms_sorry")
    ok, message = lean_axioms_clean(lean_root, declarations=("TemplateActiveInference.thm",))
    assert ok is False
    assert "sorryAx" in message


def test_lean_axioms_clean_rejects_non_whitelisted_axioms(lean_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LAKE_STUB_MODE", "axioms_native")
    ok, message = lean_axioms_clean(lean_root, declarations=("TemplateActiveInference.thm",))
    assert ok is False
    assert "Lean.ofReduceBool" in message


def test_lean_axioms_clean_fails_when_elaboration_fails(lean_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LAKE_STUB_MODE", "axioms_error")
    ok, message = lean_axioms_clean(lean_root, declarations=("TemplateActiveInference.thm",))
    assert ok is False
    assert "#print axioms run failed" in message
    assert not (lean_root / "lean" / "_AxiomCheck.lean").exists(), "checker cleanup runs on failure too"
