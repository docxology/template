"""Smoke tests for thin project scripts."""

from __future__ import annotations

import os
import py_compile
import subprocess
import sys
from pathlib import Path

SCRIPT_NAMES = (
    "run_autoresearch_loop.py",
    "z_generate_manuscript_variables.py",
    "check_source_ledger.py",
    "regenerate_mnist_fixture.py",
)


def _script_source(project_root: Path, name: str) -> str:
    return (project_root / "scripts" / name).read_text(encoding="utf-8")


def test_project_scripts_use_shared_bootstrap(project_root: Path) -> None:
    for name in SCRIPT_NAMES:
        source = _script_source(project_root, name)
        assert "from _bootstrap import ensure_project_paths" in source
        assert "sys.path.insert" not in source


def test_run_autoresearch_loop_script_is_thin_orchestrator(project_root: Path) -> None:
    script = project_root / "scripts" / "run_autoresearch_loop.py"
    py_compile.compile(str(script), doraise=True)

    source = _script_source(project_root, script.name)
    assert "from src.loop import run_autoresearch_loop" in source
    assert "run_autoresearch_loop(PROJECT_ROOT, REPO_ROOT)" in source


def test_check_source_ledger_script_is_thin_orchestrator(project_root: Path) -> None:
    script = project_root / "scripts" / "check_source_ledger.py"
    py_compile.compile(str(script), doraise=True)

    source = _script_source(project_root, script.name)
    assert "from src.source_ledger import" in source
    assert "validate_source_ledger_contract(PROJECT_ROOT)" in source


def test_regenerate_mnist_fixture_script_is_thin_orchestrator(project_root: Path) -> None:
    script = project_root / "scripts" / "regenerate_mnist_fixture.py"
    py_compile.compile(str(script), doraise=True)

    source = _script_source(project_root, script.name)
    assert "from src.ml.mnist_fixture import regenerate_mnist_fixture" in source
    assert "regenerate_mnist_fixture(PROJECT_ROOT)" in source


def test_manuscript_variable_script_writes_resolved_sources(project_root: Path) -> None:
    script = project_root / "scripts" / "z_generate_manuscript_variables.py"
    env = {
        key: value
        for key, value in os.environ.items()
        if not (key.startswith("COV_CORE_") or key.startswith("COVERAGE_"))
    }
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=project_root,
        text=True,
        capture_output=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert "manuscript_variables.json" in result.stdout
