"""Real pinned Lean controls for the standalone bounded gate."""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

import pytest

from gates.lean import build_lean, lean_axioms_clean, lean_project_present


def _project(root: Path, proof: str = "trivial") -> Path:
    """Write a real dependency-free Lean package, preserving the production pin."""
    lean = root / "lean"
    modules = lean / "TemplateActiveInference"
    modules.mkdir(parents=True)
    (lean / "lean-toolchain").write_text("leanprover/lean4:v4.14.0\n")
    (lean / "lake-manifest.json").write_text(
        json.dumps(
            {
                "version": "1.1.0",
                "packagesDir": ".lake/packages",
                "packages": [],
                "name": "TemplateActiveInference",
                "lakeDir": ".lake",
            }
        )
    )
    (lean / "lakefile.lean").write_text(
        "import Lake\nopen Lake DSL\npackage «TemplateActiveInference» where\nlean_lib «TemplateActiveInference» where\n"
    )
    (lean / "TemplateActiveInference.lean").write_text("import TemplateActiveInference.Basic\n")
    (modules / "Basic.lean").write_text(
        f"namespace TemplateActiveInference\ntheorem thm : True := by {proof}\nend TemplateActiveInference\n"
    )
    return root


def test_absent_lean_is_blocked_and_cannot_grant_axiom_acceptance(tmp_path: Path) -> None:
    assert not lean_project_present(tmp_path)
    code, message = build_lean(tmp_path)
    assert code == 75 and "blocked" in message
    ok, message = lean_axioms_clean(tmp_path)
    assert not ok and "blocked" in message


def test_actual_pinned_lean_build_and_complete_axiom_audit(tmp_path: Path) -> None:
    root = _project(tmp_path)
    assert lean_project_present(root)
    code, output = build_lean(root)
    assert code == 0, output
    ok, output = lean_axioms_clean(root, declarations=("TemplateActiveInference.thm",))
    assert ok, output
    assert "does not depend on any axioms" in output
    assert not list((root / "lean").glob("*AxiomCheck*"))


@pytest.mark.parametrize("proof", ["sorry", "native_decide", "exact False.elim False.intro"])
def test_real_unproved_unsound_or_invalid_proof_cannot_grant_audit(tmp_path: Path, proof: str) -> None:
    root = _project(tmp_path, proof)
    ok, output = lean_axioms_clean(root, declarations=("TemplateActiveInference.thm",))
    assert not ok, output


def test_exact_requested_declaration_must_exist(tmp_path: Path) -> None:
    root = _project(tmp_path)
    ok, output = lean_axioms_clean(root, declarations=("TemplateActiveInference.invented",))
    assert not ok, output
    ok, output = lean_axioms_clean(root, declarations=())
    assert not ok and "invalid" in output


def test_changed_pin_and_missing_installed_tool_are_not_silent_acquisition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    (root / "lean" / "lean-toolchain").write_text("leanprover/lean4:v4.34.1\n")
    code, output = build_lean(root)
    assert code == 2 and "pin" in output
    (root / "lean" / "lean-toolchain").write_text("leanprover/lean4:v4.14.0\n")
    monkeypatch.setenv("PATH", str(tmp_path / "no-tools"))
    code, output = build_lean(root)
    assert code == 75 and "blocked" in output


def test_zero_deadline_is_invalid(tmp_path: Path) -> None:
    code, output = build_lean(_project(tmp_path), timeout=0)
    assert code == 2 and "timeout" in output


@pytest.mark.parametrize("kind", ["source-directory", "lean-root", "source-leaf"])
def test_linked_source_cannot_hide_in_ignored_lake_cache(tmp_path: Path, kind: str) -> None:
    root = _project(tmp_path / "project")
    lean = root / "lean"
    if kind == "lean-root":
        target = tmp_path / "other-lean"
        shutil.move(str(lean), target)
        lean.symlink_to(target, target_is_directory=True)
    else:
        cached = lean / ".lake/authored"
        cached.mkdir(parents=True)
        source = lean / "TemplateActiveInference"
        if kind == "source-leaf":
            source /= "Basic.lean"
            target = cached / "Basic.lean"
        else:
            target = cached / "TemplateActiveInference"
        shutil.move(str(source), target)
        source.symlink_to(target, target_is_directory=kind == "source-directory")
    code, output = build_lean(root, timeout=30)
    assert code == 2 and "symlink" in output
    accepted, output = lean_axioms_clean(root, declarations=("TemplateActiveInference.thm",), timeout=30)
    assert not accepted and "symlink" in output
    assert not (lean / ".lake/build").exists()


@pytest.mark.parametrize("relative", ["TemplateActiveInference/Declared.lean", "lean-toolchain", "lakefile.lean"])
def test_nonregular_lean_input_is_refused_before_read_or_child_launch(tmp_path: Path, relative: str) -> None:
    root = _project(tmp_path / "project")
    source = root / "lean" / relative
    source.unlink(missing_ok=True)
    os.mkfifo(source)
    start = time.monotonic()
    code, output = build_lean(root, timeout=2)
    assert code == 2 and "regular" in output
    assert time.monotonic() - start < 2
    assert not (root / "lean/.lake").exists()


def test_actual_pinned_build_consumes_frozen_lean_despite_original_input_aba(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path / "project")
    source = root / "lean/TemplateActiveInference/Basic.lean"
    original = source.read_bytes()
    real_elan = shutil.which("elan")
    assert real_elan, "the actual declared Lean tool is required"
    adapter_dir = tmp_path / "actual-elan-adapter"
    adapter_dir.mkdir()
    observation = tmp_path / "consumed-input.json"
    adapter = adapter_dir / "elan"
    adapter.write_text(
        f"#!{sys.executable}\nimport hashlib,json,subprocess,sys\nfrom pathlib import Path\n"
        f"source=Path({str(source)!r}); original=source.read_bytes(); active='build' in sys.argv\n"
        "try:\n"
        " if active:\n"
        "  source.write_bytes(b'invalid mutable Lean input')\n"
        "  consumed=Path.cwd()/'TemplateActiveInference/Basic.lean'\n"
        f"  Path({str(observation)!r}).write_text(json.dumps({{'cwd':str(Path.cwd()),'original_changed':source.read_bytes()!=original,'consumed_sha256':hashlib.sha256(consumed.read_bytes()).hexdigest()}}))\n"
        f" code=subprocess.run([{real_elan!r}]+sys.argv[1:]).returncode\n"
        "finally:\n if active: source.write_bytes(original)\nraise SystemExit(code)\n"
    )
    adapter.chmod(0o700)
    monkeypatch.setenv("PATH", str(adapter_dir) + os.pathsep + os.environ["PATH"])
    code, output = build_lean(root, timeout=60)
    assert code == 0 and "consumed frozen Lean source SHA256" in output, output
    actual = json.loads(observation.read_text())
    import hashlib

    assert actual["original_changed"] and Path(actual["cwd"]) != source.parents[1]
    assert actual["consumed_sha256"] == hashlib.sha256(original).hexdigest()
    assert source.read_bytes() == original
    assert not (root / "lean/.lake").exists()
