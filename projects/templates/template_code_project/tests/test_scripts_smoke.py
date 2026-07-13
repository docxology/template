"""Smoke tests for auxiliary pipeline scripts (non-gated)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_generate_api_docs_writes_reference() -> None:
    """generate_api_docs.py is aesthetic-only but should run without error."""
    script = PROJECT_ROOT / "scripts" / "generate_api_docs.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    api_ref = PROJECT_ROOT / "output" / "docs" / "api_reference.md"
    assert api_ref.is_file()
    body = api_ref.read_text(encoding="utf-8")
    assert "gradient_descent" in body.lower()


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
