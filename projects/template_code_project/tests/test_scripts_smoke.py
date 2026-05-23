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
    """00_preflight.py is aesthetic-only; exit 1 is OK when chrome cache is absent."""
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
    assert any(token in combined for token in ("preflight", "puppeteer", "mmdc"))
