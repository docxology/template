"""Smoke tests for auxiliary pipeline scripts (non-gated)."""

from __future__ import annotations

import subprocess
import shutil
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_generate_api_docs_writes_reference(tmp_path: Path) -> None:
    """The actual script writes only its disposable project copy."""
    project = tmp_path / "project"
    project.mkdir()
    for directory in ("scripts", "src", "manuscript"):
        shutil.copytree(PROJECT_ROOT / directory, project / directory, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(PROJECT_ROOT / "pyproject.toml", project / "pyproject.toml")
    canonical = PROJECT_ROOT / "output" / "docs" / "api_reference.md"
    before = canonical.read_bytes() if canonical.exists() else None
    script = project / "scripts" / "generate_api_docs.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT.parents[2])
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    api_ref = project / "output" / "docs" / "api_reference.md"
    assert api_ref.is_file()
    body = api_ref.read_text(encoding="utf-8")
    assert "gradient_descent" in body.lower()
    assert (canonical.read_bytes() if canonical.exists() else None) == before


def test_preflight_script_emits_diagnostics() -> None:
    """00_preflight.py is aesthetic-only; exit 0 when no render mermaid, exit 1 when chrome absent."""
    script = PROJECT_ROOT / "scripts" / "00_preflight.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode in (0, 1), result.stderr or result.stdout
    combined = f"{result.stdout}\n{result.stderr}".lower()
    if result.returncode == 1:
        assert any(token in combined for token in ("preflight", "puppeteer", "mmdc"))


def test_run_api_doc_generation_continues_when_glossary_index_fails(tmp_path: Path) -> None:
    """Glossary index failure is logged; static api_reference.md still written."""
    repo_root = PROJECT_ROOT.parent.parent
    src_path = str(PROJECT_ROOT / "src")
    for path in (str(repo_root), src_path):
        if path not in sys.path:
            sys.path.insert(0, path)

    scripts_dir = str(PROJECT_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import generate_api_docs as api_docs_mod

    def _fail(_src: str) -> list:
        raise ValueError("glossary index unavailable")

    project_root = tmp_path
    (project_root / "src").mkdir()
    result = api_docs_mod.run_api_doc_generation(project_root, api_index_builder=_fail)
    assert result is not None
    api_ref = project_root / "output" / "docs" / "api_reference.md"
    assert api_ref.is_file()
    assert result["glossary"] is None
    assert result["api_reference"] == str(api_ref)
